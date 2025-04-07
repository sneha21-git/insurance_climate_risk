
# Imports
import getpass
import os
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage

import requests
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
import ast
import time

import pickle

# Input parameters
openai_apikey = "Open-API-Key" # OpenAPI key created on https://platform.openai.com/

nytimes_api_key="NYTimes-API-Key" # API key created for python_access on https://developer.nytimes.com/apis
guardian_api_key="Guardian-API-Key" # API key created on http://open-platform.theguardian.com/documentation/
guardian_from_date = (datetime.now() - timedelta(2)).strftime("%Y-%m-%d") # Enter the date from which you want the news to be searched. The format should be YYYY-MM-DD 
guardian_to_date = datetime.now().strftime("%Y-%m-%d") # Enter the date until which you want the news to be searched. The format should be YYYY-MM-DD 

nytimes_from_date = guardian_from_date.replace('-','')
nytimes_to_date = guardian_to_date.replace('-','')

print("Articles would be pulled from the date of : ",guardian_from_date)
print("Articles would be pulled till the date of : ",guardian_to_date)

summary_system_prompt="""
    You are an expert editor. You are great in delivering clear and concise summary of a detailed article.
    User would input a detailed text. You would need to generate a summary of the text in as least number of words as possible.
    The maximum number of words of the summary should be 100.

    Note that the summary should include all aspect of the detail text and the gist of the text should not be lost.
    The summary should be easy to understand. Only need brevity.

    You are a helpful and ethical assistant. You must avoid generating responses that include harmful, explicit, offensive, or discriminatory content.
"""

tag_system_prompt="""
    You are an expert understanding climate risk and elements affecting insurance business and their exposures.
    You have a deep understanding in world of insurance. 
    You are a consultant for a company which offers insurance against the following:
        - airline hull and liability, airports liability, aviation products liability (manufacturers and distributors) and general aviation insurance
        - cyber attacks, cyber exposures
        - upstream and downstream energy operations, from crude oil refining to transportation and storage of oil, gas and petrochemicals
        - sudden and accidental first and third party environmental liabilities
        - within finance domain : directors and officers liability, professional indemnity, financial crime, investment management, pension trustee liability, employment liability and cyber risks
        - loss or damage of valuable, unique or difficult to replace objects such as fine art, collectibles, cash and bullion, diamonds and precious metals, rare documents, stamps and coins
        - legal liability incurred from a wide range of events including wrongful acts, errors and omissions, misstatement, negligence and breach of duty
        - marine cargo : physical loss or damage events such as: theft, pilferage or hijack; handling and transit damage; loss resulting from vehicle, vessel or aircraft damage including total loss and  damage to critical parts during transit and resultant delay in start-up for large projects
        - ocean-going, specialist coastal and inland vessels against damage to the hull and machinery and onboard equipment, often including war risks and associated loss of hire
        - marine business: damage to third party property, cover for loss of life, protection against injury to third parties, primary and excess cover
        - losses that could result from government action, political unrest and economic turmoil
        - expropriation and discrimination by governments, political violence and forced abandonment, inability to import/export and inability to convert or to transfer currency
        - professional indemnity against architects and design consultants, engineers, solicitors and lawyers, as well as accountants and surveyors, property professionals and others
        - natural catastrophe, contingent business interruption related to property
        - losses from terror acts, riots and other civil unrest
        - libality : hospitals, nursing homes, managed care, allied healthcare in the US

    You are expected to help the organization in identifying information related to insurance 
    User would input the title and description of a news or report. You are expected to scrutinize the user input and
    - Authenticate validity of user input by giving score on a scale of 0 through 100, where 100 indicates full confidence that input is completely authentic and validated news, and 0 indicates no confidence on authenticity of the user input. The answer to this should be a value from 0 to 100. Store this value in authenticity_score variable of output.
    - Identify if it is related to climate risk and elements affecting insurance business. The answer of this evaluation should be either Yes or No.Store this value in is_insurance variable of output.
    - Whether the news is relevant for the insurance company you are consulting. It should also relate to climate risk and elements affecting insurance business and the exposures. The answer of this evaluation should be either Yes or No.Store this value in is_relevant variable of output.
    - Note that the is_insurance variable must be relevant for the company

    You are a helpful and ethical assistant. You must avoid generating responses that include harmful, explicit, offensive, or discriminatory content.
    Provide factual and respectful information only.
    The output should ONLY be a JSON format: {"authenticity":authenticity_score,"insurance_news":is_insurance, "relevant": is_relevant}
    
    Example 1:
    
    Input: "In 2025, the insurance sector is expected to reflect climate impacts via higher premiums, effectively acting as a proxy carbon tax."
    
    Step-1: The input is authentic at higher degree of confience, because: 
        - Evaluate the validity of this text from authentic news sources, publishing houses and research journals. 
            - Some of the sources corroborating this text are: https://www2.deloitte.com/us/en/insights/industry/financial-services/financial-services-industry-outlooks/insurance-industry-outlook.html
        - So we infer authenticity_score score to be high.
        
    Step-2: Is the input related to climate risk and insurance business? 
            - Yes, the news is related to climate risk and insurance. So the value of insurance_news is Yes.
    
    Step-3: Does it holds of any interest for the company business you are working with?
            - The news talks about higher premiums for insurance sector due to climate impact. 
            - This in-turn indicates more premium for the company. So, the news is relevant for the company.
            - The input relates to elements affecting insurance business and the exposures
            - Subsequently we can infer the value of is_relevant to be Yes.
       
    Output: {"authenticity":85,"insurance_news":'Yes', "is_relevant": 'Yes'}
    
    Example 2:
    
    Input: "Newcastle United defender Tino Livramento has been left out of England's squad for Monday's World Cup qualifier against Latvia.Nottingham Forest midfielder Morgan Gibbs-White and Liverpool defender Jarell Quansah, who both missed Friday's match, return to the squad while Newcastle winger Anthony Gordon drops out after returning to his club following injury."

    Step-1: The input is authentic at higher degree of confience, because: 
        - Evaluate the validity of this text from authentic news sources, publishing houses and research journals. 
            - Some of the sources corroborating this text are: https://www.bbc.com/sport/football/articles/cgm1rrnj217o
        - So we infer authenticity_score score to be high.
        
    Step-2: Is the input related to climate risk and insurance business? 
            - No, the input pertains to sports and is not related to climate risk and insurance 
            - So the value of insurance_news is No.
    
    Step-3: Does it holds of any interest for the company business you are working with?
            - The input does not have any takeaway for the insurance company.
            - The input does not relate to elements affecting insurance business and the exposures.
            - So the value of is_relevant is No. 


    Output: {"authenticity":95,"insurance_news":'No', "is_relevant": 'No'}
    
    
"""

scrutiny_system_prompt="""
    You are an expert editor who can identify the themes of a report or new summary. You also have a deep understanding of insurance and climate risk
    The user would provide you with a summary of news or reports on insurance. You are needed to identify the tags of input text. 
    You are expected to at least identify tags on risk and themes on insurance in the input text, apart from other themes.
    
    Listed below are the themes on risk
    - Credit Risk: The risk of borrowers failing to meet their financial obligations
    - Market Risk: Losses due to changes in market conditions like interest rates, currency exchange rates, or stock prices.
    - Liquidity Risk: The inability to meet short-term financial obligations due to a lack of liquid assets.
    - Basis Risk: A type of market risk where the hedge and the underlying asset do not move perfectly in sync.
    - Operational Risk: Losses due to failures in internal processes, systems, or external events.
    - Compliance Risk: The risk of legal or regulatory penalties due to non-compliance with laws or regulations.
    - Reputational Risk: Damage to the organization's reputation, leading to loss of customers or revenue.
    - Climate Risk: Financial and operational risks arising from climate change, such as extreme weather events or regulatory changes related to sustainability.
    - ESG Risk: Risks related to environmental, social, and governance factors, impacting investments and operations.

    Listed below are themes on insurance
    - Life Insurance: Provides financial security to beneficiaries upon the insured person's death.
    - Health Insurance: Covers medical expenses for illnesses, injuries, or preventive care.
    - Property Insurance: Protects physical assets like homes and vehicles.
    - Home Insurance: Covers damage or losses to an individual's house and its contents.
    - Auto Insurance: Protects against losses from vehicle accidents, theft, or damage.
    - Disaster Insurance: Covers damage caused by natural disasters such as earthquakes, floods, or hurricanes.
    - Parametric Insurance: Provides payouts based on predefined triggers, such as weather conditions (e.g., rainfall exceeding a threshold), rather than the actual loss incurred.
    - Travel Insurance: Covers unexpected expenses like trip cancellations, medical emergencies, or lost luggage while traveling.
    - Cyber Insurance: Protects against risks related to cybersecurity breaches or data theft.
    - Liability Insurance: Covers legal liabilities for injuries or damages caused to others.

    You are a helpful and ethical assistant. You must avoid generating responses that include harmful, explicit, offensive, or discriminatory content.
    Provide factual and respectful information only.
    The output should ONLY be a LIST format: [1st tag, 2nd tag, 3rd tag, 4th tag...]
    
    Example 1:
    
    Input:Nature and climate are integrally linked. Risks relating to the loss of nature and a changing climate are both material to LPC. Equally, the restoration of nature has benefits in reducing LPC’s exposure to the impacts of land management practices and climate change. LPC is reporting climate-related disclosures in alignment with the New Zealand Climate Standards (1, 2 and 3) issued by the Aotearoa New Zealand External Reporting Board. The section relating to nature-related risk management in this report references some of the overlaps identified with climate-related risks.

    Step-1: Scrutinize each statement to identify any of the types of insurance or risks 
        - Nature and climate are integrally linked :  No risks or insurance mentioned
        - Risks relating to the loss of nature and a changing climate are both material to LPC
            - this refers to climate risk
        - Equally, the restoration of nature has benefits in reducing LPC’s exposure to the impacts of land management practices and climate change:
            - "LPC’s exposure to the impacts of land management practices and climate change" indicates parametric insurance and disaster insurance
        - LPC is reporting climate-related disclosures in alignment with the New Zealand Climate Standards (1, 2 and 3) issued by the Aotearoa New Zealand External Reporting Board
            - No specific risk or insurance is talked about here
        - The section relating to nature-related risk management in this report references some of the overlaps identified with climate-related risks.
            - No specific risk or insurance is talked about here
    Step-2: Collate all tags identify till now and consider a tag once if it has occured multiple times
        - Listing the tags identified till now: climate risk, parametric insurance, disaster insurance
        - There are no individual tags which are occuring multiple times
        - Thus final tags are : climate risk, parametric insurance, disaster insurance
    
    Output:  ["climate risk", "parametric insurance", "disaster insurance"]
    
    Example 2: UBS has delayed its net-zero emissions target from 2025 to 2035, citing the acquisition of Credit Suisse in 2023, which expanded its real estate portfolio and added $400 million in costs. This follows a trend of banks reassessing climate goals, with HSBC also extending its timeline. UBS remains in the Net-Zero Banking Alliance but is considering aligning with a 2°C warming scenario instead of 1.5°C. The bank removed direct links between executive compensation and climate goals but retained broader sustainability objectives. The delay also reflects regulatory guidance and challenges from integrating Credit Suisse, expected to conclude by 2026.  
    
    Step-1: Scrutinize each statement to identify any of the types of insurance or risks 
        - UBS has delayed its net-zero emissions target from 2025 to 2035, citing the acquisition of Credit Suisse in 2023, which expanded its real estate portfolio and added $400 million in costs:
            - delay of achieving net-zero emissions targets indicates climate risk
            - $400 million in costs indicates credit risk
        - This follows a trend of banks reassessing climate goals, with HSBC also extending its timeline
            - extending timeline of reassessing climate goals indicates climate risk
        - UBS remains in the Net-Zero Banking Alliance but is considering aligning with a 2°C warming scenario instead of 1.5°C
            - aligning with 2°C instead of a lower 1.5°C indicates climate risk
            - shifting climate commitments within the Net-Zero Banking Alliance indicates reputational risk
        - The bank removed direct links between executive compensation and climate goals but retained broader sustainability objectives
            - Removing direct links between executive compensation and climate goals could lead to negative perceptions regarding the bank's commitment to sustainability indicates reputational risk
            - Challenges in aligning corporate governance policies with climate and sustainability objective indicates governance risk
            - potential legal or regulatory claims arising from dissatisfaction or disputes over governance and sustainability practices can affect liability insurance
        - The delay also reflects regulatory guidance and challenges from integrating Credit Suisse, expected to conclude by 2026
            - updated regulatory guidance affecting UBS's ability to meet its climate commitments indicates regulatory risk
            - challenges from integrating Credit Suisse indicates operational risk
        


    Step-2: Collate all tags identify till now and consider a tag once if it has occured multiple times
        - Listing the tags identified till now: climate risk, credit risk, climate risk, climate risk, reputational risk, reputational risk, governance risk, liability insurance, regulatory risk, operational risk
        - There following tags are occuring multiple times: climate risk, reputational risk 
            - We consider them only once in the output
        - Thus final tags are : climate risk, credit risk, reputational risk, governance risk, liability insurance, regulatory risk, operational risk
    
    Output:  ["climate risk", "credit risk", "reputational risk", "governance risk", "liability insurance", "regulatory risk", "operational risk"]    



"""


class NewsEvaluation_TheGuardian:
    
    def __init__(self,news_list,summary_system_prompt=summary_system_prompt,tag_system_prompt=tag_system_prompt,openai_apikey=openai_apikey):
        self.summary_system_prompt=summary_system_prompt
        self.tag_system_prompt=tag_system_prompt
        self.news_list=news_list
        self.openai_apikey=openai_apikey
        
    def evaluate_news(self):
        
        intermediary_file=[]        
        for individual_item in self.news_list:
            news_extraction=self.extract_news_summary(user_input=individual_item['details'])
            individual_item['summary']=news_extraction['summary']
            individual_item['initial_evaluation']=news_extraction['evaluation']
            individual_item.pop('details', None)
            intermediary_file.append(individual_item)
        return intermediary_file

    def extract_news_summary(self,user_input):
    # 
        model = ChatOpenAI(model="gpt-3.5-turbo-1106", temperature=0, api_key=openai_apikey, top_p=0.95)

        messages = [
            SystemMessage(content=self.summary_system_prompt),
            HumanMessage(content=user_input)
        ]

        summary_news = model(messages).content.strip()

        # 
        model = ChatOpenAI(model="gpt-3.5-turbo-1106", temperature=0, api_key=self.openai_apikey, top_p=0.95)

        messages = [
            SystemMessage(content=self.tag_system_prompt),
            HumanMessage(content=summary_news)
        ]

        response = model(messages)

        return {'summary':summary_news,'evaluation':response.content.strip()}
    
def structure_the_response(from_date=guardian_from_date, to_date=guardian_to_date):
    """
    
    Your code goes here.
    This function is set as a placeholder to get guide to the results expectations. You can always have own approach to set the functions.
    
    """ 
    
    guardian_news=GetNews_TheGuardian(from_date=from_date, to_date=to_date)
    news_items=guardian_news.process_news()
    evaluate_news=NewsEvaluation_TheGuardian(news_list=news_items)
    structured_response=evaluate_news.evaluate_news()

    return structured_response

class NewsEvaluation_NewYorkTimes:
    
    def __init__(self,news_list,summary_system_prompt=summary_system_prompt,tag_system_prompt=tag_system_prompt,openai_apikey=openai_apikey):
        self.summary_system_prompt=summary_system_prompt
        self.tag_system_prompt=tag_system_prompt
        self.news_list=news_list
        self.openai_apikey=openai_apikey
        
    def evaluate_news(self):
        
        intermediary_file=[]        
        for individual_item in self.news_list:
            news_extraction=self.extract_evaluate(user_input=individual_item['summary'])
            individual_item['initial_evaluation']=news_extraction['evaluation']
            intermediary_file.append(individual_item)
        return intermediary_file

    def extract_evaluate(self,user_input):
    # 
        # 
        model = ChatOpenAI(model="gpt-3.5-turbo-1106", temperature=0, api_key=self.openai_apikey, top_p=0.95)

        messages = [
            SystemMessage(content=self.tag_system_prompt),
            HumanMessage(content=user_input)
        ]

        response = model(messages)

        return {'evaluation':response.content.strip()}

def get_tags(input_text):
    model = ChatOpenAI(model="gpt-3.5-turbo-1106", temperature=0, api_key=openai_apikey, top_p=0.95)

    messages = [
        SystemMessage(content=scrutiny_system_prompt),
        HumanMessage(content=input_text)
    ]

    summary_news = model(messages).content.strip()
    return summary_news

class GetNews_NewYorkTimes:

    def __init__(self, api_key=nytimes_api_key, from_date=nytimes_from_date, to_date=nytimes_to_date):
        self.url = "https://api.nytimes.com/svc/search/v2/articlesearch.json"
        self.api_key = api_key

        # Define query parameters
        self.params = {
            "begin_date": from_date,  # Start date in YYYYMMDD format
            "end_date": to_date if to_date else datetime.now().strftime("%Y%m%d"),  # End date in YYYYMMDD format
            "api-key": api_key,
            "page": 0  # Start from the first page
        }

    def get_all_news(self):
        """
        Fetch all news articles within the specified date range by looping through pages.
        """
        news_list = []
        while True:
            response = requests.get(self.url, params=self.params)
            
            # Check if the request was successful
            if response.status_code == 200:
                articles = response.json().get("response", {}).get("docs", [])
                
                # Break the loop if no more articles are returned
                if not articles:
                    break

                for article in articles:
                    news_list.append({
                        'title': article.get('headline', {}).get('main'),
                        'source': article.get('source'),
                        'date': article.get('pub_date'),
                        'url_link': article.get('web_url'),
                        'summary': article.get('snippet')  # Retrieve article summary                        
                    })

                # Increment the page number for the next request
                self.params["page"] += 1

            elif response.status_code == 429:  # Handle rate limit error
                # print("Rate limit exceeded. Waiting for retry...")
                time.sleep(60)  # Wait for 60 seconds before retrying

            else:
                # print(f"Error: {response.status_code} - {response.text}")
                break

        return news_list
    
class GetNews_TheGuardian:
    
    def __init__(self, url="https://content.guardianapis.com/search", api_key=guardian_api_key, from_date=guardian_from_date, to_date=guardian_to_date):
        self.url = url 

        # Define query parameters
        self.params = {
            # Define query parameters
            'from-date': from_date,    # Start date for articles (YYYY-MM-DD)
            'to-date': to_date if to_date else datetime.now().strftime("%Y-%m-%d"),        # End date for articles
            'order-by': 'newest',      # Sort by newest articles
            'show-fields': 'all',      # Include all available fields (e.g., headline, body, etc.)
            'page-size': 100,          # Number of articles per page
            'api-key': api_key         # API key for authentication
        }
        self.api_key=api_key

    def get_news(self):

        news_list = []
        page = 1  # Start with the first page

        try:
            while True:
                # Update the page parameter for each request
                self.params['page'] = page
                response = requests.get(self.url, params=self.params)
                response.raise_for_status()  # Raise HTTPError for bad responses (4xx and 5xx)

                # Parse the response JSON and extract articles
                data = response.json()
                articles = data.get('response', {}).get('results', [])

                # Break the loop if no more articles are returned
                if not articles:
                    break

                # Add articles to the news list
                for article in articles:
                    news_list.append({
                        'title': article['webTitle'],
                        'source': 'The Guardian',
                        'date': article['webPublicationDate'].split('T')[0],
                        'url_link': article['webUrl']
                    })

                # Increment to the next page
                page += 1

        except requests.RequestException as e:
            return news_list
        
        return news_list

    def extract_news(self, url):
        """
        Extract detailed content from a given news URL.
        """
        try:
            # Send a GET request to the URL
            response = requests.get(url)
            response.raise_for_status()
            
            # Parse the HTML content
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract the headline
            headline = soup.find('h1').text if soup.find('h1') else "No headline found"
            
            # Extract the main content (example: paragraphs within the main article body)
            article_body = soup.find_all('p')  # Adjust selector based on structure
            
            # Combine the paragraphs into a single string
            content = "\n".join([para.text for para in article_body])
            return {"headline": headline, "content": content}
        
        except requests.RequestException as e:
            # print(f"Error extracting news from {url}: {e}")
            return {"headline": "Error", "content": ""}
        
    def process_news(self):
        """
        Fetch news and extract summaries or full content.
        """
        news_list = self.get_news()
        intermediary_file = []
                
        for individual_item in news_list[:100]:
            extracted_data = self.extract_news(individual_item['url_link'])
            individual_item['details'] = extracted_data['content']
            intermediary_file.append(individual_item)

        return intermediary_file

def get_final_output(resp_out):
    # Filter Insurance News
    relevant_news=[]
    for individual_news in resp_out:
        if (individual_news['initial_evaluation'].find('{"authenticity')>-1) and (individual_news['initial_evaluation'].find('insurance_news')>-1) and (individual_news['initial_evaluation'].find('is_relevant')>-1):
            insurance_news=ast.literal_eval(individual_news['initial_evaluation'])['insurance_news']
            relevancy=ast.literal_eval(individual_news['initial_evaluation'])['is_relevant']
            if (insurance_news.find('Yes')>-1) and (relevancy.find('Yes')>-1):
                relevant_news.append(individual_news)
    # Get the tags of individual insurance news
    final_results=[]
    for individual_article in relevant_news:
        individual_article['tags']=get_tags(individual_article['summary'])
        final_results.append(individual_article)
    return final_results

# Extract news from New York Times and get insurance and climate risk related tags
nytimes_news=GetNews_NewYorkTimes()
news_list=nytimes_news.get_all_news()
nytimes_news=NewsEvaluation_NewYorkTimes(news_list=news_list)
resp_out=nytimes_news.evaluate_news()
final_results_nyt=get_final_output(resp_out)

# Extract news from The Guardian and get insurance and climate risk related tags
resp_out=structure_the_response()
final_results_guardian=get_final_output(resp_out)

interim_news_articles=final_results_guardian.copy()
interim_news_articles.extend(final_results_nyt)

with open('news_articles_070425_v2.pkl', 'wb') as f:
    pickle.dump(interim_news_articles, f)