HAMLET E COMMERCE PRIVATE LIMITED - Tally Prime import pack, FY 2025-26
=======================================================================

BEFORE IMPORT
1. Open the company in Tally Prime (books from 01-Apr-2025, GST enabled, State = Haryana,
   GSTIN 06AADCH7641A1ZZ). Take a backup of the company data first.
2. If your company already has these bank ledgers under a different name, rename them to
   exactly:  HDFC Bank - 50200059929011  |  HDFC Bank - 50200015831844  |  Kotak Mahindra Bank - 9599195566
   (or the import will create new bank ledgers with these names).

IMPORT ORDER  (Gateway of Tally > Import > Masters / Transactions, or Alt+O > Import)
   1. 01_Masters_Ledgers.xml            -> Import > Masters   (choose "Ignore Duplicates" if asked)
   2. 02_Purchases_GSTR2B.xml           -> Import > Transactions
   3. 03_Bank_Vouchers.xml              -> Import > Transactions
   4. 04_RCM_Liability_Journals.xml     -> Import > Transactions

WHAT IS IN EACH FILE
- 01: 322 ledgers. GST suppliers carry GSTIN, state and address from GSTR-2B (bill-wise on).
      Tax ledgers: Input CGST / Input SGST / Input IGST / Input Cess (Duties & Taxes, GST duty head set).
      Purchase ledgers per rate: Purchase GST @ 0.25% / 1.5% / 3% / 5% / 12% / 18%, Purchase GST @ 0% (exempt),
      Purchase - RCM @ 5% (reverse charge flag on), Purchase GST - Mixed Rate (no fixed rate).
- 02: 213 purchase vouchers (accounting-invoice mode), one per GSTR-2B B2B line, numbered PUR/2526/0001..
      (was 736: the 523 lines at 18% are now Journal vouchers in file 10 - see "18% PURCHASES AS JOURNALS" below).
      Supplier invoice no. and date are in Reference / Reference Date; bill-wise New Ref = invoice no.
      Voucher date = invoice date when the invoice falls in the same month as its 2B period; otherwise the
      last day of the 2B period month (93 invoices, listed in the review workbook) so ITC lands in the
      GSTR-3B month in which it appears in 2B.
      ITC "No" lines (16, POS mismatch): tax booked to "GST Input - Ineligible (ITC Not Available)" not to input tax.
      Porter (78 lines) are reverse charge: party credited with taxable value only.
- 03: 989 Payment + 545 Receipt + 81 Contra vouchers using your voucher numbers (HDFC9011-n / HDFC1844-n / KTK-n).
      Transfers between the three accounts are posted ONCE as Contra (the mirror row is dropped).
- 04: 5 monthly Journals booking RCM liability on Porter (Dr Input IGST - RCM / Cr RCM Liability Payable - IGST).
      Open each journal once in Tally, press F12/Ctrl+O > Stat Adjustment and confirm nature
      "Increase of Tax Liability & Input Tax Credit" if Tally did not pick it up from the file.
      RCM must be paid in cash (Table 3.1(d) of GSTR-3B) before the ITC is taken.

AFTER IMPORT - CHECKLIST FOR FILING
- GSTR-3B (Display > Statutory Reports > GST > GSTR-3B): Table 4(A)(5) should show the ITC totals given in
  00_Review_and_Control_Totals.xlsx > Summary. Resolve anything under "Uncertain Transactions":
  the 8 "Mixed-rate" invoices need a rate typed in (list in the workbook).
- 00_Review_and_Control_Totals.xlsx > "Needs review (bank)" lists every bank line still parked in Suspense A/c
  (828 lines, mostly UPI / marketplace settlements) - reclassify in Tally as you confirm them.
- "Exceptions" sheet: 7 receipts your sheet labelled as internal transfers are actually third-party credits,
  and 3 GSTR-2B invoices whose value does not equal taxable + tax.
- Opening balances as on 01-Apr-2025 are NOT in this pack (not in the source files) - enter them in the
  bank / party ledgers separately.
- Sales (GSTR-1) is not covered: the files contain only bank statements and purchase (2B) data.


SALES PACK (added later) - files 05 to 08
=========================================
Import AFTER files 01-04, in this order (Import > Masters for 05, Import > Transactions for the rest):
   5. 05_Sales_Masters.xml               -> choose "Modify with New Data" (it re-defines Amazon.com, eBay.com,
                                            Tejasvini Chander, Manokamna Jewellers, Seher Munjal..., Putta Chidvilas,
                                            S P Enterprises, MIRA GEMS as Sundry Debtors with country/state/GSTIN)
   6. 06_Sales_Direct_HEC.xml            -> 123 HEC/25-26 invoices (23 domestic with CGST/SGST or IGST, 100 exports)
   7. 07_Sales_Amazon_FBA_Monthly.xml    -> 12 monthly Amazon FBA export invoices (GEM/25-26/APR ... MAR)
   8. 08_Sales_Marketplace_Q1..Q4.xml    -> 11,225 marketplace export orders (GEM/25-26/1 ... 11263), one per quarter

Before importing vouchers: Gateway > Alter > Voucher Type > Sales - set "Method of voucher numbering" to Manual
(or Automatic (Manual Override)) so the invoice numbers in the files are kept. Do the same for Purchase, Payment,
Receipt, Contra, Journal if you have not already imported files 02-04.

How the sales are classified
- Domestic: state from GSTIN (B2B) or from the address (B2C). Haryana -> Output CGST + Output SGST; other states -> Output IGST.
  Sales ledgers are per HSN and rate (Sales - Domestic HSN 7113 @ 3% etc.) so the GSTR-1 HSN summary comes out right.
- Exports (direct, marketplace, FBA): party ledger carries the foreign country and the sales line is marked
  "Exports LUT/Bond" - zero tax, reported in GSTR-1 Table 6A / GSTR-3B 3.1(b). Amounts are the INR values from the
  sheet; the foreign-currency amount and rate are in the narration (no multi-currency masters were created).
- Marketplace and FBA export ledgers use HSN 71041000 @ 0.25% (from the FBA sheet and the sheet title). Change the
  HSN on those two ledgers if your goods differ - every voucher follows the ledger.
- Round-off up to Rs.1 goes to "Round Off"; larger invoice adjustments go to "Discount / Adjustment on Sales"
  (4 invoices, listed in 00b_Sales_Review_and_Control_Totals.xlsx > Exceptions).

Things to check after import (all listed in 00b_Sales_Review_and_Control_Totals.xlsx)
- HEC/25-26/124 (GIA/Kaeleff Kuspa) has zero value and was skipped.
- HEC/25-26/73 (RAMAN) is marked United Kingdom but has a Gurugram address and 1.5% GST - booked as Haryana B2C.
- 308 marketplace orders are in INR inside the export sheet - booked as exports as per the sheet; confirm.
- Bank receipts from pack 1 posted to "Export Sales", "Ebay Payment", "Tazapay Canada Corp", "POS Payment Settlement"
  etc. are the collections against Amazon.com / eBay.com; re-point them to the debtor ledgers when reconciling.

IF SALES / PURCHASE LEDGERS ARE NOT CREATED ON IMPORT (added 12-Sep-2026)
------------------------------------------------------------------------
05_Sales_Masters.xml now creates every ledger WITHOUT GST rate details (plain ledgers under Sales Accounts etc.).
After it imports, either:
  (a) import 05b_Sales_Ledgers_GST_Rates_ALTER.xml (Import > Masters, "Modify with New Data") to push the
      HSN/rate details onto the 17 sales ledgers, or
  (b) set them by hand from the sheet "Sales ledger GST setup" in 00b_Sales_Review_and_Control_Totals.xlsx
      (Alter Ledger > GST applicable: Applicable > Set/alter GST details > HSN, Taxable, rate).
If the purchase ledgers from file 01 were also missing, import 01b_Purchase_and_Tax_Ledgers_PLAIN.xml the same way
and set the rates on the 9 purchase ledgers (Purchase GST @ 0.25% ... 18%, Purchase - RCM @ 5%) by hand.


18% PURCHASES AS JOURNALS (added 25-Sep-2026) - files 09 and 10
==============================================================
The 523 vouchers that debited "Purchase GST @ 18%" are no longer Purchase vouchers. Each one is now a
Journal voucher that debits the expense ledger for that creditor (as per the "Tally Ladger Name" sheet),
debits the input tax, and credits the supplier bill-wise - the same shape as the sample journal:
      Dr  Shipping Exp 18%                                 1,058.00
      Dr  Input IGST                                         190.44
          Cr  Busybees Logistics Solutions Private Limited            1,248.44
Numbering: JV/2526/0001 .. JV/2526/0523 in voucher-date order. The narration keeps the GSTR-2B period, the
supplier invoice and the old purchase number (e.g. "was Purchase PUR/2526/0044"). Supplier invoice no./date
stay in Reference / Reference Date; bill-wise New Ref = invoice no. Round-off and "GST Input - Ineligible"
lines are carried over unchanged. Nothing else in the pack changed (totals credited to suppliers are the same).

New / changed files
   09_Expense_Ledgers_Masters.xml  -> Import > Masters. Creates 7 ledgers under Indirect Expenses, GST applicable,
                                      Taxable @ 18% (Services; "Packing Material Purchase 18%" = Goods):
                                      Shipping Exp 18% | Business EXP | Office Rent Exp 18% | Software Exp 18% |
                                      Other Services Exp 18% | Packing Material Purchase 18% | Travel Exp 18%
                                      Choose "Ignore Duplicates" if some already exist in the company.
   09b_Expense_Ledgers_PLAIN.xml   -> same 7 ledgers WITHOUT GST details - use only if 09 does not create them
                                      (then set GST applicable / 18% by hand, as for 01b / 05b).
   10_Expense_Journals_18pct.xml   -> Import > Transactions. 523 Journal vouchers. Set Voucher Type "Journal"
                                      numbering to Manual (or Automatic (Manual Override)) first, as for the others.
   02_Purchases_GSTR2B.xml         -> REPLACED: now holds only the 213 purchase vouchers at other rates
                                      (0% / 0.25% / 1.5% / 3% / 5% / 12% / mixed / RCM). The previous version is
                                      kept as 02_Purchases_GSTR2B_ORIGINAL_with_18pct.xml for reference - do not import it.
   expense_ledger_mapping.csv      -> creditor -> expense ledger -> group (42 rows, from the "Tally Ladger Name" sheet).
                                      Edit this and re-run _generator_convert_18pct_to_journal.py to change a mapping.

Import order (fresh company): 01, 09, 02, 10, 03, 04, then the sales pack 05-08.

IF THE OLD 02 WAS ALREADY IMPORTED: delete the 523 Purchase vouchers first, then import 09 and 10.
   The list is in 00_Review_and_Control_Totals.xlsx > "Purchase vchs replaced" (PUR number, date, supplier, amount,
   and the JV number that replaces it). Quickest way in Tally: Gateway > Display More Reports > Account Books >
   Ledger > "Purchase GST @ 18%" > F12 set "Show narrations" off, select all (Ctrl+Space) > Alt+D. Its closing
   balance must be zero before you import file 10. The ledger "Purchase GST @ 18%" itself can stay (unused) or be deleted.

Control totals (00_Review_and_Control_Totals.xlsx > "18% Expense Journals", per ledger and per month):
   Journals 523 | Dr expense 64,29,180.58 | Dr input tax 11,57,253.75 | Cr suppliers 75,86,434.50
After import, GSTR-3B Table 4(A)(5) must still show the same ITC as before: the input tax ledgers and amounts are
unchanged, only the debit side moved from "Purchase GST @ 18%" to the expense ledgers. If the journals do not appear
in GSTR-3B, open one and confirm the party / GST details are picked up (Ctrl+I or F12 > "Provide GST details").
