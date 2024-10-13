import re
import argparse
import tomllib
import hmac
import hashlib
import requests
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from notion_client import Client


app = FastAPI()


class Commit(BaseModel):
    message: str
    url: str


class Push(BaseModel):
    commits: list[Commit]


def verify_github_signature(payload_body: bytes, signature: str) -> bool:
    expected_signature = 'sha256=' + hmac.new(
        args.github_webhook_secret.encode(), payload_body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected_signature, signature)


def get_notion_page_id(ticket_id: str) -> str:
    try:
        return notion.databases.query(
            **{
                "database_id": f"{args.notion_database_id}",
                "filter": {
                    "property": "ID",
                    "unique_id": {
                        "equals": int(ticket_id),
                    },
                },
            }
        )['results'][0]['id']
    except KeyError:
        return None


def update_notion_ticket(page_id: str, commit_message: str, commit_url: str) -> bool:
    notion.comments.create(
        **{
            "parent": { "page_id": page_id },
            "rich_text": [
                {
                    "text": {
                        "content": f"New commit: {commit_message}\n"
                    }
                },
                {
                    "text": {
                        "content": "url",
                        "link": {
                            "url": f"{commit_url}"
                        }
                    },
                }
            ]
        }
    )


@app.post("/sync")
async def webhook(request: Request, push: Push):
    signature = request.headers.get('X-Hub-Signature-256')
    payload_body = await request.body()

    if not signature or not verify_github_signature(payload_body, signature):
        raise HTTPException(status_code=400, detail="Invalid signature")

    for commit in push.commits:
        matches = re.search(r'(#PM-(\d+))', commit.message)
        if matches:
            ticket_id = matches.group(2)

            page_id = get_notion_page_id(ticket_id)
            print("Page ID:", page_id)
            if page_id is not None:
                update_notion_ticket(page_id, commit.message, commit.url)
            print(f"Commit: {commit.message}")

    return JSONResponse(content={"status": "success"}, status_code=200)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-c", "--config", required=True)
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("-p", "--port", type=int, default=8000)
    args = parser.parse_args()

    with open(args.config, 'rb') as f:
        data = tomllib.load(f)
        args.github_webhook_secret = data["github"]["webhook_secret"]
        args.notion_api_key = data["notion"]["api_key"]
        args.notion_database_id = data["notion"]["database_id"]

    notion = Client(auth=args.notion_api_key)

    import uvicorn
    uvicorn.run(app, host=args.host, port=args.port)

