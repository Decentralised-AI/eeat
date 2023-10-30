import os
import re
import json
from serpapi import GoogleSearch
from langchain.chat_models import ChatOpenAI
from langchain.schema import SystemMessage, HumanMessage

from utils import *

SERPAPI_KEY = os.environ.get('SERPAPI_KEY')
OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')
INDUSTRY_KEYWORD = "Vector database"

if not SERPAPI_KEY:
    print("Please set the SERPAPI_KEY environment variable.")
    exit()

def extract_company_urls_from_serp(serp_content, industry_query):
    
    chat = ChatOpenAI(temperature=0, model_name="gpt-3.5-turbo-0613")
    messages = [
        SystemMessage(content="Analyse SERP and Identify company-specific domains based on a given Google search query. '"+industry_query+"'. Return only list of urls if found. Return only urls without quotes etc."),
        HumanMessage(content=f" {serp_content} \n\n The urls list: ")
    ]

    try:
        response = chat(messages)
        gpttitle = response.content
    except Exception as e:
        print(f"An error occurred: {e}")
        return "Not found"

    # Remove the quotation marks from the start and end of the generated title
    if gpttitle[0] == '"':
        gpttitle = gpttitle[1:]
    if gpttitle[-1] == '"':
        gpttitle = gpttitle[:-1]
    
    return gpttitle

def search_companies_on_google(industry_query):
    params = {
        "engine": "google",
        "q": industry_query,
        'gl': 'us',
        'hl': 'en',
        'num': 20,
        "api_key": SERPAPI_KEY,
    }
    search = GoogleSearch(params)
    results = search.get_dict()

    # Error handling for missing key
    if "organic_results" in results:
        return results["organic_results"]
    else:
        print("Error: 'organic_results' not found in the results!")
        print(results)  # This will print the structure of results to inspect it
        return []

def main():
    industry_query = INDUSTRY_KEYWORD
    print(industry_query + "\n")
    organic_results = search_companies_on_google(industry_query)
    print(organic_results)
    
    # Setting the folder based on the industry keyword
    directory_name = os.path.join('data', INDUSTRY_KEYWORD)
    
    serp_content = ""
    for result in organic_results:
        if "snippet" not in result:
            result["snippet"] = ""
        serp_content += (str(result["position"]) + ". " + result["link"] + " " + result["title"] + " " + result["snippet"])
            
    company_urls = extract_company_urls_from_serp(serp_content, industry_query)

    # Assuming the returned URLs are separated by commas or spaces
    url_list = re.split(r'[,\s]+', company_urls)

    company_domains = {}
    for url in url_list:
        domain = extract_domain_from_url(url)
        if domain:  # Ensuring domain is not empty
            company_domains[domain] = {'url': url}

    save_to_json_file(company_domains, 'companies.json', directory_name)
    print(f"Company data saved to {directory_name}/companies.json")

if __name__ == '__main__':
    main()