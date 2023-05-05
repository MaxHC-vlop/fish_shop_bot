import requests

from textwrap import dedent


def fetch_access_token(client_id, client_secret):
    url = 'https://api.moltin.com/oauth/access_token'
    data = {
        'client_id': client_id,
        'client_secret': client_secret,
        'grant_type': 'client_credentials',
    }
    response = requests.post(url, data=data)
    response.raise_for_status()
    access_token = response.json()['access_token']

    return access_token


def get_all_products(access_token):
    url = 'https://api.moltin.com/pcm/products'
    headers = {'Authorization': f'Bearer {access_token}'}
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    data_response = response.json()['data']
    products = {}
    for product in data_response:
        products[product['attributes']['name']] = product['id']

    return products


def get_product_detail(access_token, product_id):
    url = f'https://api.moltin.com/pcm/products/{product_id}'
    headers = {'Authorization': f'Bearer {access_token}'}
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    product_detail = response.json()['data']['attributes']['description']

    return product_detail


def get_file_id(access_token, product_id):
    url = f'https://api.moltin.com/pcm/products/{product_id}/relationships/main_image'
    headers = {'Authorization': f'Bearer {access_token}'}
    response = requests.get(url, headers=headers)
    response.raise_for_status()

    file_id = response.json()['data']['id']

    return file_id


def get_image_link(access_token, file_id):
    url = f'https://api.moltin.com/v2/files/{file_id}'
    headers = {'Authorization': f'Bearer {access_token}'}
    response = requests.get(url, headers=headers)
    response.raise_for_status()

    image_link = response.json()['data']['link']['href']

    return image_link


def get_cart(access_token, cart_name):
    url = f'https://api.moltin.com/v2/carts/{cart_name}/items'
    headers = {
        'Authorization': f'Bearer {access_token}'
    }

    response = requests.get(url, headers=headers)
    response.raise_for_status()
    cart_items = response.json()
    cart_info = {}
    cart_info['total_price'] = cart_items['meta']['display_price']['with_tax']['formatted']
    cart_info['products'] = {}
    for item in cart_items['data']:
        item_detail = {item['id']: {
                'price': item['meta']['display_price']['with_tax']['unit']['formatted'],
                'total': item['meta']['display_price']['with_tax']['value']['formatted'],
                'quantity': item['quantity'],
                'name': item['name']
            }
        }
        cart_info['products'].update(item_detail)

    return cart_info


def add_product_to_cart(access_token, cart_name, product, quantity):
    url = f'https://api.moltin.com/v2/carts/{cart_name}/items'
    headers = {
        'Authorization': f'Bearer {access_token}'
    }
    payload = {
        'data': {
            'id': product,
            'type': 'cart_item',
            'quantity': quantity
        }
    }
    response = requests.post(url, headers=headers, json=payload)
    response.raise_for_status()


def formated_message(items):
    template_message = '''\
        {name}
        {price} per kg
        {quantity}kg in cart for {total}\n
    '''
    message = ''
    products = items['products']
    for product in products:
        temmplate = dedent(template_message.format_map(products[product]))
        message += temmplate

    total_price = items['total_price']
    message += f'total {total_price}'
    if total_price == '0':
        message = 'Cart is empty'

    return message


def remove_item_from_cart(access_token, cart_id, product_id):
    url = f'https://api.moltin.com/v2/carts/{cart_id}/items/{product_id}'
    headers = {
        'Authorization': f'Bearer {access_token}'
    }
    response = requests.delete(url, headers=headers)
    response.raise_for_status()


def make_client(access_token, name, email):
    url = 'https://api.moltin.com/v2/customers'
    headers = {
        'Authorization': f'Bearer {access_token}'
    }
    payload = {
        'data': {
            'type': 'customer',
            'name': name,
            'email': email,
        }
    }
    response = requests.post(url, headers=headers, json=payload)
    response.raise_for_status()
