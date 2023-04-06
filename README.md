# daily-arxiv-slackbot

Automatically Update NLP Papers Daily using Slackbot (ref: Vincentqyw/cv-arxiv-daily, monologg/nlp-arxiv-daily)

## How to use

### Prerequisites

1. OpenAI API Key
2. Slack Web hook url, channel id, and access token

### Setting up

1. Please make a json file with your slack tokens and fill `sample_slack_key.json` file. ( Rename it if you want )

```json
{
  "SLACK": {
    "WEB_HOOK_URL": "web_hook_url",
    "CHANNEL": "your_channel",
    "ACCESSED_TOKEN": "xoxb-accesse_token"
  },
  "TEST_SLACK": {
    "WEB_HOOK_URL": "web_hook_url",
    "CHANNEL": "your_test_channel",
    "ACCESSED_TOKEN": "xoxb-accesse_token"
  }
}
```

2. Please write down your OpenAI API key and your workspace path in the .env file.

```env
OPENAI_API_KEY=your_openai_key_starts_with_sk
WORKSPACE=repository_on_your_local
SLACK_TOKEN_FILE=your_slack_token_filename.json
```

3. Install the required packages.

```bash
pip install -r requirements.txt
```

4. Run !
```python
python main.py
```