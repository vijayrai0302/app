"""
Convert the "Purchase GST @ 18%" purchase vouchers in 02_Purchases_GSTR2B.xml into
Journal vouchers booked to expense ledgers (Shipping Exp 18%, Business EXP, ...).

Inputs  (all in the pack folder unless overridden on the command line):
  02_Purchases_GSTR2B.xml            - purchase vouchers built by _generator_build_tally.py
  expense_ledger_mapping.csv         - Creditor name -> Expense ledger -> Tally group
                                       (exported from the "Tally Ladger  Name" sheet of hamlet_18_purchase_1.xls;
                                        pass the .xls/.xlsx instead of the csv to read that sheet directly)
Outputs (written into the pack folder):
  09_Expense_Ledgers_Masters.xml     - the expense ledgers, Indirect Expenses, GST applicable @ 18%
  09b_Expense_Ledgers_PLAIN.xml      - same ledgers without GST rate details (fallback, see README)
  10_Expense_Journals_18pct.xml      - one Journal per former 18% purchase voucher
  02_Purchases_GSTR2B.xml            - rewritten WITHOUT the converted vouchers (original kept as
                                       02_Purchases_GSTR2B_ORIGINAL_with_18pct.xml)
  00_Review_and_Control_Totals.xlsx  - three sheets added: "18% Expense Journals",
                                       "Expense ledger mapping", "Purchase vchs replaced"

Usage:  python3 _generator_convert_18pct_to_journal.py [pack_folder] [mapping_file]
"""
import sys, os, csv, re, shutil, datetime, collections, unicodedata
import xml.etree.ElementTree as ET
from xml.sax.saxutils import escape

PACK = sys.argv[1] if len(sys.argv) > 1 else os.path.dirname(os.path.abspath(__file__))
MAPPING = sys.argv[2] if len(sys.argv) > 2 else os.path.join(PACK, 'expense_ledger_mapping.csv')
SRC_LEDGER = 'Purchase GST @ 18%'
JV_PREFIX = 'JV/2526/'
TAX_LEDGERS = {'Input CGST', 'Input SGST', 'Input IGST', 'Input Cess', 'GST Input - Ineligible (ITC Not Available)'}
# ledgers whose supply is goods rather than services (drives GSTTYPEOFSUPPLY on the master)
GOODS_LEDGERS = {'Packing Material Purchase 18%'}
RATE = 18


def ascii_(s):
    if s is None:
        return ''
    s = str(s).replace('–', '-').replace('—', '-').replace('’', "'").replace('‘', "'").replace('“', '"').replace('”', '"')
    s = unicodedata.normalize('NFKD', s).encode('ascii', 'ignore').decode()
    return re.sub(r'\s+', ' ', s).strip()


def x(s):
    return escape(ascii_(s))


def amt(v):
    return f"{v:.2f}"


def norm(s):
    return re.sub(r'\s+', ' ', ascii_(s)).strip().lower()


# ---------------- mapping ----------------
def load_mapping(path):
    """returns {creditor(normalised): (creditor, expense ledger, group)}"""
    rows = []
    if path.lower().endswith(('.xls', '.xlsx')):
        import openpyxl
        wb = openpyxl.load_workbook(path, data_only=True)
        sheet = next((ws for ws in wb.worksheets if 'ladger' in ws.title.lower() or 'ledger' in ws.title.lower()), None)
        if sheet is None:
            sys.exit('mapping sheet ("Tally Ladger  Name") not found in ' + path)
        for r in sheet.iter_rows(min_row=2, values_only=True):
            if r[1] and r[2]:
                rows.append((r[1], r[2], r[3] or 'Indirect Expenses'))
    else:
        with open(path, newline='', encoding='utf-8') as f:
            rd = csv.DictReader(f)
            for r in rd:
                if r.get('Creditor Name') and r.get('Expense Ledger'):
                    rows.append((r['Creditor Name'], r['Expense Ledger'], r.get('Under Tally Group') or 'Indirect Expenses'))
    mp = {}
    for cred, led, grp in rows:
        mp[norm(cred)] = (ascii_(cred), ascii_(led), ascii_(grp))
    return mp


mapping = load_mapping(MAPPING)
if not mapping:
    sys.exit('empty mapping: ' + MAPPING)

# ---------------- read purchase vouchers ----------------
src_path = os.path.join(PACK, '02_Purchases_GSTR2B.xml')
orig_path = os.path.join(PACK, '02_Purchases_GSTR2B_ORIGINAL_with_18pct.xml')
if os.path.exists(orig_path):
    src_path = orig_path            # re-runnable: always start from the untouched file
else:
    shutil.copyfile(src_path, orig_path)

with open(src_path, encoding='utf-8') as f:
    raw = f.read()
# split into TALLYMESSAGE blocks so the untouched vouchers are written back byte-for-byte
head, rest = raw.split('<REQUESTDATA>\n', 1)
body, tail = rest.rsplit('</REQUESTDATA>', 1)
blocks = re.findall(r'<TALLYMESSAGE xmlns:UDF="TallyUDF">\n.*?</TALLYMESSAGE>\n', body, flags=re.S)
assert ''.join(blocks) == body, 'unexpected layout in 02_Purchases_GSTR2B.xml'

keep, convert, unmapped = [], [], []
for b in blocks:
    v = ET.fromstring(b).find('VOUCHER')
    lines = [(le.findtext('LEDGERNAME'), float(le.findtext('AMOUNT')), le) for le in v.findall('LEDGERENTRIES.LIST')]
    if not any(n == SRC_LEDGER for n, _, _ in lines):
        keep.append(b)
        continue
    party = v.findtext('PARTYLEDGERNAME')
    m = mapping.get(norm(party))
    if m is None:
        unmapped.append((v.findtext('VOUCHERNUMBER'), party))
        keep.append(b)
        continue
    convert.append((v, lines, m))

if unmapped:
    print('WARNING - creditors without an expense ledger in the mapping (left as Purchase vouchers):')
    for vno, p in unmapped:
        print('   ', vno, p)

# ---------------- build journals ----------------
HEAD = '<?xml version="1.0" encoding="UTF-8"?>\n<ENVELOPE>\n<HEADER>\n<TALLYREQUEST>Import Data</TALLYREQUEST>\n</HEADER>\n<BODY>\n<IMPORTDATA>\n<REQUESTDESC>\n<REPORTNAME>{rep}</REPORTNAME>\n</REQUESTDESC>\n<REQUESTDATA>\n'
TAIL = '</REQUESTDATA>\n</IMPORTDATA>\n</BODY>\n</ENVELOPE>\n'


def entry(ledger, amount, billname=None, billtype=None, partyflag=False):
    dr = amount < 0
    s = [f'<ALLLEDGERENTRIES.LIST>\n<LEDGERNAME>{x(ledger)}</LEDGERNAME>\n<ISDEEMEDPOSITIVE>{"Yes" if dr else "No"}</ISDEEMEDPOSITIVE>\n']
    if partyflag:
        s.append('<ISPARTYLEDGER>Yes</ISPARTYLEDGER>\n')
    s.append(f'<AMOUNT>{amt(amount)}</AMOUNT>\n')
    if billtype:
        s.append(f'<BILLALLOCATIONS.LIST>\n<NAME>{x(billname or "")}</NAME>\n<BILLTYPE>{billtype}</BILLTYPE>\n<AMOUNT>{amt(amount)}</AMOUNT>\n</BILLALLOCATIONS.LIST>\n')
    s.append('</ALLLEDGERENTRIES.LIST>\n')
    return ''.join(s)


journals = []      # for the review workbook
# number the journals in voucher-date order, then by the original purchase number
convert.sort(key=lambda t: (t[0].findtext('DATE'), t[0].findtext('VOUCHERNUMBER')))
seq = 0
out = [HEAD.format(rep='Vouchers')]
for v, lines, (cred, exp_ledger, grp) in convert:
    seq += 1
    vno = f'{JV_PREFIX}{seq:04d}'
    date = v.findtext('DATE')
    party = v.findtext('PARTYLEDGERNAME')
    inv = v.findtext('REFERENCE') or ''
    old_vno = v.findtext('VOUCHERNUMBER')
    narr = ascii_(v.findtext('NARRATION')) + f' | Expense booked to {exp_ledger} (was Purchase {old_vno})'
    extra = (f'<REFERENCE>{x(inv)}</REFERENCE>\n<REFERENCEDATE>{v.findtext("REFERENCEDATE")}</REFERENCEDATE>\n'
             f'<PARTYLEDGERNAME>{x(party)}</PARTYLEDGERNAME>\n<PARTYNAME>{x(party)}</PARTYNAME>\n'
             f'<PARTYGSTIN>{x(v.findtext("PARTYGSTIN"))}</PARTYGSTIN>\n<STATENAME>{x(v.findtext("STATENAME"))}</STATENAME>\n'
             f'<PLACEOFSUPPLY>{x(v.findtext("PLACEOFSUPPLY"))}</PLACEOFSUPPLY>\n<GSTREGISTRATIONTYPE>Regular</GSTREGISTRATIONTYPE>\n')
    out.append(f'<TALLYMESSAGE xmlns:UDF="TallyUDF">\n<VOUCHER VCHTYPE="Journal" ACTION="Create" OBJVIEW="Accounting Voucher View">\n'
               f'<DATE>{date}</DATE>\n<EFFECTIVEDATE>{date}</EFFECTIVEDATE>\n<VOUCHERTYPENAME>Journal</VOUCHERTYPENAME>\n'
               f'<VOUCHERNUMBER>{x(vno)}</VOUCHERNUMBER>\n<NARRATION>{x(narr)}</NARRATION>\n<PERSISTEDVIEW>Accounting Voucher View</PERSISTEDVIEW>\n{extra}')
    # debits first (expense, then tax, then round off), party credit last - same order as the sample journal
    taxable = tax = other = 0.0
    party_amt = None
    for name, a, le in lines:
        if name == SRC_LEDGER:
            out.append(entry(exp_ledger, a)); taxable += -a
        elif name == party:
            bill = le.find('BILLALLOCATIONS.LIST')
            party_amt = a
    for name, a, le in lines:
        if name in TAX_LEDGERS:
            out.append(entry(name, a)); tax += -a
    for name, a, le in lines:
        if name not in TAX_LEDGERS and name not in (SRC_LEDGER, party):
            out.append(entry(name, a)); other += -a
    assert party_amt is not None, old_vno
    bill = [le for n, a, le in lines if n == party][0].find('BILLALLOCATIONS.LIST')
    out.append(entry(party, party_amt, billname=bill.findtext('NAME') if bill is not None else inv,
                     billtype=bill.findtext('BILLTYPE') if bill is not None else 'New Ref', partyflag=True))
    assert abs(taxable + tax + other - party_amt) < 0.01, (old_vno, taxable, tax, other, party_amt)
    out.append('</VOUCHER>\n</TALLYMESSAGE>\n')
    journals.append(dict(vno=vno, old=old_vno, date=datetime.datetime.strptime(date, '%Y%m%d').date(), party=party,
                         inv=inv, ledger=exp_ledger, taxable=round(taxable, 2), tax=round(tax, 2), other=round(other, 2), total=round(party_amt, 2),
                         period=re.search(r'GSTR-2B (\w+\'\d\d)', narr).group(1) if re.search(r'GSTR-2B (\w+\'\d\d)', narr) else ''))
out.append(TAIL)
with open(os.path.join(PACK, '10_Expense_Journals_18pct.xml'), 'w', encoding='utf-8') as f:
    f.write(''.join(out))

# ---------------- rewrite 02 without the converted vouchers ----------------
with open(os.path.join(PACK, '02_Purchases_GSTR2B.xml'), 'w', encoding='utf-8') as f:
    f.write(head + '<REQUESTDATA>\n' + ''.join(keep) + '</REQUESTDATA>' + tail)

# ---------------- expense ledger masters ----------------
exp_ledgers = collections.OrderedDict()
for cred, led, grp in mapping.values():
    exp_ledgers.setdefault(led, grp)


def ledger_xml(name, parent, with_gst):
    n = x(name); p = x(parent)
    s = [f'<TALLYMESSAGE xmlns:UDF="TallyUDF">\n<LEDGER NAME="{n}" RESERVEDNAME="" ACTION="Create">\n<NAME.LIST TYPE="String"><NAME>{n}</NAME></NAME.LIST>\n<PARENT>{p}</PARENT>\n<AFFECTSSTOCK>No</AFFECTSSTOCK>\n']
    if with_gst:
        supply = 'Goods' if name in GOODS_LEDGERS else 'Services'
        s.append(f'<GSTAPPLICABLE>&#4; Applicable</GSTAPPLICABLE>\n<GSTTYPEOFSUPPLY>{supply}</GSTTYPEOFSUPPLY>\n<GSTDETAILS.LIST>\n<APPLICABLEFROM>20250401</APPLICABLEFROM>\n<CALCULATIONTYPE>On Value</CALCULATIONTYPE>\n<TAXABILITY>Taxable</TAXABILITY>\n<ISREVERSECHARGEAPPLICABLE>No</ISREVERSECHARGEAPPLICABLE>\n<STATEWISEDETAILS.LIST>\n<STATENAME>&#4; Any</STATENAME>\n')
        for head, val in (('Central Tax', RATE / 2), ('State Tax', RATE / 2), ('Integrated Tax', RATE), ('Cess', 0)):
            s.append(f'<RATEDETAILS.LIST>\n<GSTRATEDUTYHEAD>{head}</GSTRATEDUTYHEAD>\n<GSTRATEVALUATIONTYPE>Based on Value</GSTRATEVALUATIONTYPE>\n<GSTRATE>{val:g}</GSTRATE>\n</RATEDETAILS.LIST>\n')
        s.append('</STATEWISEDETAILS.LIST>\n</GSTDETAILS.LIST>\n')
    s.append('</LEDGER>\n</TALLYMESSAGE>\n')
    return ''.join(s)


for fname, with_gst in (('09_Expense_Ledgers_Masters.xml', True), ('09b_Expense_Ledgers_PLAIN.xml', False)):
    with open(os.path.join(PACK, fname), 'w', encoding='utf-8') as f:
        f.write(HEAD.format(rep='All Masters'))
        for led, grp in exp_ledgers.items():
            f.write(ledger_xml(led, grp, with_gst))
        f.write(TAIL)

# ---------------- review workbook ----------------
import openpyxl
from openpyxl.styles import Font
wb_path = os.path.join(PACK, '00_Review_and_Control_Totals.xlsx')
wb = openpyxl.load_workbook(wb_path)
for title in ('18% Expense Journals', 'Expense ledger mapping', 'Purchase vchs replaced'):
    if title in wb.sheetnames:
        del wb[title]

ws = wb.create_sheet('18% Expense Journals')
ws.append(['Purchase GST @ 18% vouchers re-booked as Journal vouchers (file 10_Expense_Journals_18pct.xml)'])
ws['A1'].font = Font(bold=True, size=13)
ws.append([])
ws.append(['Control totals', 'Journals', 'Taxable (Dr expense)', 'Input tax (Dr)', 'Round off / other (Dr)', 'Credited to suppliers'])
ws.append(['All', len(journals), round(sum(j['taxable'] for j in journals), 2), round(sum(j['tax'] for j in journals), 2),
           round(sum(j['other'] for j in journals), 2), round(sum(j['total'] for j in journals), 2)])
ws.append([])
ws.append(['Per expense ledger', 'Journals', 'Taxable (Dr expense)', 'Input tax (Dr)', 'Round off / other (Dr)', 'Credited to suppliers'])
for led in exp_ledgers:
    js = [j for j in journals if j['ledger'] == led]
    ws.append([led, len(js), round(sum(j['taxable'] for j in js), 2), round(sum(j['tax'] for j in js), 2),
               round(sum(j['other'] for j in js), 2), round(sum(j['total'] for j in js), 2)])
ws.append([])
ws.append(['Per month (voucher date)', 'Journals', 'Taxable (Dr expense)', 'Input tax (Dr)', 'Round off / other (Dr)', 'Credited to suppliers'])
for ym in sorted({(j['date'].year, j['date'].month) for j in journals}):
    js = [j for j in journals if (j['date'].year, j['date'].month) == ym]
    ws.append([f'{ym[0]}-{ym[1]:02d}', len(js), round(sum(j['taxable'] for j in js), 2), round(sum(j['tax'] for j in js), 2),
               round(sum(j['other'] for j in js), 2), round(sum(j['total'] for j in js), 2)])
ws.append([])
ws.append(['Journal no.', 'Date', 'Was purchase vch', '2B period', 'Supplier', 'Supplier invoice', 'Expense ledger (Dr)', 'Taxable', 'Input tax', 'Round off / other', 'Credited to supplier'])
for j in journals:
    ws.append([j['vno'], j['date'].isoformat(), j['old'], j['period'], j['party'], j['inv'], j['ledger'], j['taxable'], j['tax'], j['other'], j['total']])

ws2 = wb.create_sheet('Expense ledger mapping')
ws2.append(['Creditor (Sundry Creditors ledger)', 'Expense ledger (Dr in journal)', 'Under Tally group', 'Journals', 'Taxable booked'])
for cred, led, grp in mapping.values():
    js = [j for j in journals if norm(j['party']) == norm(cred)]
    ws2.append([cred, led, grp, len(js), round(sum(j['taxable'] for j in js), 2)])
ws2.append([])
ws2.append(['Ledgers created by 09_Expense_Ledgers_Masters.xml', 'Parent group', 'GST', 'Type of supply'])
for led, grp in exp_ledgers.items():
    ws2.append([led, grp, f'Applicable, Taxable @ {RATE}%', 'Goods' if led in GOODS_LEDGERS else 'Services'])

ws3 = wb.create_sheet('Purchase vchs replaced')
ws3.append(['If 02_Purchases_GSTR2B.xml (old version) was already imported: DELETE these Purchase vouchers in Tally before importing file 10'])
ws3['A1'].font = Font(bold=True)
ws3.append(['Purchase vch no.', 'Date', 'Supplier', 'Supplier invoice', 'Amount', 'Replaced by journal'])
for j in sorted(journals, key=lambda j: j['old']):
    ws3.append([j['old'], j['date'].isoformat(), j['party'], j['inv'], j['total'], j['vno']])

for w in (ws, ws2, ws3):
    for col in w.columns:
        w.column_dimensions[col[0].column_letter].width = min(60, max(12, max(len(str(c.value or '')) for c in col) + 2))
wb.save(wb_path)

print(f'converted {len(journals)} purchase vouchers -> journals; {len(keep)} purchase vouchers kept in 02; '
      f'{len(exp_ledgers)} expense ledgers; taxable {round(sum(j["taxable"] for j in journals), 2)}; '
      f'credited to suppliers {round(sum(j["total"] for j in journals), 2)}; unmapped {len(unmapped)}')
