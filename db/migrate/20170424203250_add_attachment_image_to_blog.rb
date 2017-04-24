class AddAttachmentImageToBlog < ActiveRecord::Migration[5.0]
  def change
    add_column :blogs, :attachment, :image
  end
end
