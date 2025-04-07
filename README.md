# README

## Objective

To scan across news articles, identify the thematic tags of news which pertain to insurance or climate risk.

## Solution

The solution has three stages:
1. **Stage-1 :** News article extraction
2. **Stage-2 :** Identification of whether the article pertains to climate risk or insurance  
3. **Stage-3 :** For the identified articles, create theamatic tags  
   Examples: credit risk, market risk, parametric insurance, others.

## Required Python Environment

Python 3.13.2

### Setup Instructions

1. **Create a New Virtual Environment**  
   _Note: Skip this step if the virtual environment already exists._  
   ```bash
   python3 -m venv tracker_env
2. **Activate the Virtual Environment**
    ```bash
   tracker_env/Scripts/activate
3. **Install the python libraries needed for the solution**
    ```bash
    pip install -r requirements.txt
4. **Open the script** ***get_news.py*** **and update the following fields**
    ```bash
    openai_apikey - Open API key
    nytimes_api_key - API key to extract news from New York Times: https://developer.nytimes.com/apis 
    guardian_api_key - API key to extract news from The Guardian: http://open-platform.theguardian.com/documentation/
    guardian_from_date - Start date from which you want to scan the news(format : YYYY-MM-DD). By default the date is considered as yesterday
guardian_to_date - End date till which you want to scan the news (format : YYYY-MM-DD). By default the date is considered as today

5. **Execute the script to extract news from The Guardian and New York Times**
    ```bash
    python get_news.py

6. **Run the streamlit script to view the dashboard**
    ```bash
    streamlit run app.py