import os
from github import Github
import requests
import json
import base64

gh_token = os.environ['INPUT_GITHUB-TOKEN']
kritik_token = os.environ['INPUT_KRITIK-TOKEN']

g = Github(gh_token)
repo = g.get_repo(os.environ['GITHUB_REPOSITORY'])
gh_user = os.environ['GITHUB_ACTOR']

gh_ref = os.environ['GITHUB_REF']
if "pull/" not in gh_ref:
    exit()

def get_file_content(file, gh_token=None, gh_username=None):
    if gh_token:
        headers = {
            "Authorization": f"Token {gh_token}",
            "User-Agent": gh_username,
        }
        resp = requests.get(file.contents_url, headers=headers)
    else:
        resp = requests.get(file.contents_url)
    json_resp = json.loads(resp.content)
    assert json_resp["encoding"] == "base64", "Wrong decode format"
    content = base64.b64decode(json_resp["content"]).decode("utf-8")
    return content

pr_num = gh_ref[gh_ref.find("pull/")+len("pull/"):gh_ref.rfind("/")]
pr = repo.get_pull(int(pr_num))
commits = list(pr.get_commits())
files = list(pr.get_files())

data = {}
data["token"] = kritik_token
data["data"] = {}
for file in files:
    content = get_file_content(file, gh_token, gh_user)
    data["data"][file.filename] = {}
    data["data"][file.filename]["full_file"] = content
    data["data"][file.filename]["patch"] = file.patch

json_data = json.dumps(data)
headers = {'Content-type': 'application/json'}
response = requests.post('https://europe-west1-kritikai-27840.cloudfunctions.net/kritik_api', data=json_data, headers=headers)

if response.status_code != 200:
    print("Request error:", response.status_code)
    print(response.text)
    exit()

print("Request response:", response.text)
data = json.loads(response.text)

def create_review(token, repo, pr, body, commit_sha, filename, line_num):
    url = "https://api.github.com/repos/"+repo.full_name+"/pulls/"+pr.number+"/comments"
    headers = {
        "Accept": "application/vnd.github+json",
        "Authorization": "Bearer "+token,
        "X-GitHub-Api-Version": "2022-11-28"
    }
    data = {
        "body": body,
        "commit_id": commit_sha,
        "path": filename,
        "line": line_num,
    }
    response = requests.post(url, headers=headers, json=data)
    return response

for filename, file_data in data.items():
    for line_num, review in file_data.items():
        # find the latest commit that contributed to this change
        for commit in reversed(commits):
            resp = create_review(gh_token, repo, pr, review, commit.sha, filename, int(line_num))
            if resp.status_code == 201:
                break
