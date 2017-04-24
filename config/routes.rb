Rails.application.routes.draw do
  devise_for :admins
  devise_for :users
  resources :users
  mount Ckeditor::Engine => '/ckeditor'
	resources :posts
	root to: 'posts#index'
	resources :blogs
  # For details on the DSL available within this file, see http://guides.rubyonrails.org/routing.html
end
