import requests

from environs import Env


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
    product_detail = response.json()

    return product_detail


def get_cart(access_token, cart_name):
    url = f'https://api.moltin.com/v2/carts/{cart_name}'
    headers = {
        'Authorization': f'Bearer {access_token}'
    }

    response = requests.get(url, headers=headers)
    response.raise_for_status()


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


env = Env()
env.read_env()

client_id = env.str('CLIENT_ID')
client_secret = env.str('CLIENT_TOKEN')
access_token = fetch_access_token(client_id, client_secret)
print(get_product_detail(access_token, '832f5a1b-5f68-4bb1-9e30-c2e36395d400'))
