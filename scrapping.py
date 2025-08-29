import requests

bojautologin = ''

url = ''

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36',
    'Cookie': f'bojautologin={bojautologin};'
}

response = requests.get(url, headers=headers)

with open('test.html', 'w', encoding='utf-8') as f:
    f.write(response.text)