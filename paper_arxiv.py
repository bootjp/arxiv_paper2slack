import os
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
import arxiv
import openai
import random

SLACK_CHANNEL = "#general"
openai.api_key = os.getenv("OPENAPI_APIKEY")
SLACK_API_TOKEN = os.getenv("SLACK_API_TOKEN")

if os.getenv("SLACK_CHANNEL") is not None:
    SLACK_CHANNEL = os.getenv("SLACK_CHANNEL")


def get_summary(result):
    system = """与えられた論文の要点を3点のみでまとめ、以下のフォーマットで日本語で出力してください。```
    タイトルの日本語訳
    ・要点1
    ・要点2
    ・要点3
    ```"""

    text = f"title: {result.title}\nbody: {result.summary}"
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {'role': 'system', 'content': system},
            {'role': 'user', 'content': text}
        ],
        temperature=0.25,
    )
    summary = response['choices'][0]['message']['content']
    title_en = result.title
    title, *body = summary.split('\n')
    body = '\n'.join(body)
    date_str = result.published.strftime("%Y-%m-%d %H:%M:%S")
    return f"発行日: {date_str}\n{result.entry_id}\n{title_en}\n{title}\n{body}\n"


def main():
    client = WebClient(token=SLACK_API_TOKEN)

    query = ['cat:cs.DB', 'cat:cs.DC']
    counter = 0

    for q in query:
        search = arxiv.Search(
            query=q,
            max_results=100,
            sort_by=arxiv.SortCriterion.SubmittedDate,
            sort_order=arxiv.SortOrder.Descending,
        )

        result_list = []
        for result in search.results():
            result_list.append(result)

        num_papers = 3
        results = random.sample(result_list, k=num_papers)

        for _, result in enumerate(results):
            counter = counter + 1
            try:
                message = "今日の論文です！ " + str(counter) + "本目\n" + get_summary(result)
                response = client.chat_postMessage(
                    channel=SLACK_CHANNEL,
                    text=message
                )
                print(f"Message posted: {response['ts']}")
            except SlackApiError as e:
                print(f"Error posting message: {e}")


if __name__ == "__main__":
    main()
