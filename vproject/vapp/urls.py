from django.urls import path
from vapp import views
from django.contrib.auth import views as auth_views
from .views import user_list

urlpatterns = [

    path('', views.log_in, name="log_in"),
    path('logout/', auth_views.LogoutView.as_view(next_page='/'), name='logout'),

    path('products/', views.product_list, name='product_list'),
    path('get_products_data/', views.get_products_data, name='get_products_data'),


    # path('products/edit/<int:pk>/', views.product_edit, name='product_edit'),
    path('product_create/', views.product_create, name='product_create'),

    path('orders/', views.order_list, name='order-list'),
    path('get_orders_data/', views.get_orders_data, name='get_orders_data'),
    path('export-csv/', views.export_orders_csv, name='export-csv'),
    path('details/', views.order_details, name='order_details'),

    # path('analytics/', views.analytics, name='analytics'),

    path('settings/', views.settings, name='settings'),
    path('set_helper/', views.set_helper, name='set_helper'),
    path('stop_bot/', views.stop_bot, name='stop_bot'),
    path('set_match_time/', views.set_match_time, name='set_match_time'),
    path('message/', views.send_message_to_all, name='message'),
    path('change_bot_status/', views.change_bot_status, name='change_bot_status'),
    path('users/', user_list, name='user_list'),



  
    
]
