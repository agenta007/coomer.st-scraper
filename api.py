import requests
PROXIES = {
    #"http":  "socks5://domain_or_ip:port",
   #"https": "socks5://domain_or_ip.:port",
}
users = {
    #"username": ["discord", "user_id"],
}
# Header that was passed with curl
headers = {
    "Accept": "text/css"
}
def get_creator(platform, user_id):
    url = f"https://kemono.cr/api/v1/{platform}/user/{user_id}/profile"
    response = requests.get(url, headers=headers, proxies=PROXIES)
    response.raise_for_status()

    print("Status code:", response.status_code)
    print("Response body:")
    print(response.text)

def get_posts_creator(platform, user_id):
    '''
    curl - X
    'GET' \
    'https://kemono.cr/api/v1/patreon/user/77554620/posts' \
    - H
    'accept: application/json'
    '''
    url = f"https://kemono.cr/api/v1/{platform}/user/{user_id}/posts"
    response = requests.get(url, headers=headers, proxies=PROXIES)
    response.raise_for_status()

    print("Status code:", response.status_code)
    print("Response body:")
    print(response.text)
    return response.json()
def main():
    #get_creator(users["MrSweetCuckold"][0], users["MrSweetCuckold"][1])
    posts = get_posts_creator(users["MrSweetCuckold"][0], users["MrSweetCuckold"][1])
    for post in posts:
        print(post["title"])
if __name__ == "__main__":
    main()