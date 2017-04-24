class AddNameToBlog < ActiveRecord::Migration[5.0]
  def change
    add_column :blogs, :name, :string
  end
end
