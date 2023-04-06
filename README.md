# daily-arxiv-slackbot
Automatically Update NLP Papers Daily using Slackbot (ref: Vincentqyw/cv-arxiv-daily, monologg/nlp-arxiv-daily)


## How to use
### Insert your tokens
1. Create a slack app and get the token
2. Create a slack channel and get the channel id
3. Create a slack bot and get the bot token
4. Create a slack user and get the user token
5. Make up `sample_slack_key.json` with your slack tokens
6. Rename `sample_slack_key.json` to anything you want (e.g. `slack_key.json`)
7. Create a openAI api key
8. Insert your openAI api key into `.sample.env`
9. Rename `.sample.env` to `.env`

### Run the script
1. Install the requirements
2. Run `python main.py`
3. Enjoy your daily arxiv papers!

