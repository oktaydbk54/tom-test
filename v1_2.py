import streamlit as st
import requests
from bs4 import BeautifulSoup
from openai import OpenAI
import os

# Load your OpenAI API key
api_key = os.getenv('OPENAI_API_KEY')
client = OpenAI(api_key=api_key)

def scrape_url(url):
    response = requests.get(url)
    if response.status_code != 200:
        return 'No title found', 'No meta description found', 'No body content found'
    soup = BeautifulSoup(response.text, 'html.parser')
    title = soup.find('title').text if soup.find('title') else 'No title found'
    meta_description = soup.find('meta', attrs={'name': 'description'})
    meta_description = meta_description['content'] if meta_description else 'No meta description found'
    body = soup.get_text(separator='\n') if soup.body else 'No body content found'
    return title, meta_description, body

def generate_title_and_article(example_text, keyword):
    prompt = f"""
    Based on the following example markdown text and the primary keyword, generate a suitable title and an article body.

    Example Text:
    {example_text}

    Primary Keyword: {keyword}

    Title and Article:
    """
    response = client.chat.completions.create(
                    model="gpt-4o",
                    messages=[
                        {"role": "system", "content": "You are an expert assistant. Your job is to create a professional title and article for users. Here you have to understand the sample text and keyword values ​​given to you thoroughly and create a new title and article without changing the meaning in response to the values ​​coming from the user."},
                        {"role": "user", "content": prompt},
                    ]
                )
    response_json = response.choices[0].message.content
    return response_json

def generate_custom_tags(article, keyword, competitor_data):
    prompt = f"""
    Based on the following article and competitor data, create custom tags such as title, meta description, and article schema.

    Article:
    {article}

    Primary Keyword: {keyword}

    Competitor Data:
    {competitor_data}

    Custom Tags:
    """
    response = client.chat.completions.create(
                    model="gpt-4o",
                    messages=[
                        {"role": "system", "content": "Your task is to create custom tag words for the new article using the article and keyword values ​​you received from the user and the information from competitor sites. It is very important that it is SEO compatible and you have to reach a conclusion after evaluating the information you receive very well."},
                        {"role": "user", "content": prompt},
                    ]
                )
    response_json = response.choices[0].message.content
    return response_json

def generate_intro_paragraph(article, keyword, competitor_data):
    prompt = f"""
    Based on the following article and competitor data, write an engaging introduction paragraph.

    Article:
    {article}

    Primary Keyword: {keyword}

    Competitor Data:
    {competitor_data}

    Introduction Paragraph:
    """
    response = client.chat.completions.create(
                    model="gpt-4o",
                    messages=[
                        {"role": "system", "content": "Your task is to write an intro paragraph using the information from the users, the article, keywords, and competitor pages. While writing this text, you have to preserve all the information and meaning and always write in a way that helps the user."},
                        {"role": "user", "content": prompt},
                    ]
                )
    response_json = response.choices[0].message.content
    return response_json

def generate_toc_key_takeaways_faqs(article, keyword, competitor_data):
    prompt = f"""
    Based on the following article and competitor data, create a table of contents, key takeaways, and FAQs using the same HTML formatting as the example markdown file.

    Article:
    {article}

    Primary Keyword: {keyword}

    Competitor Data:
    {competitor_data}

    Table of Contents, Key Takeaways, and FAQs:
    """
    response = client.chat.completions.create(
                    model="gpt-4o",
                    messages=[
                        {"role": "system", "content": "Your task is to create a table of contents, key takeaways, and FAQs using the information provided and formatted in HTML."},
                        {"role": "user", "content": prompt},
                    ]
                )
    response_json = response.choices[0].message.content
    return response_json

def assemble_markdown(custom_tags, intro_paragraph, toc_key_takeaways_faqs, article):
    author = "Tom & Jess"  # Dynamic or default value
    date_published = "2024-06-11"  # Dynamic or default value
    date_modified = "2024-06-17"  # Dynamic or default value

    markdown_content = f"""
@metadata
- Author: {author}
- Date Published: {date_published}
- Date Modified: {date_modified}

@schema
{custom_tags}
@endmetadata

@toc
{toc_key_takeaways_faqs}
@endtoc

# {article['title']}

## Introduction
{intro_paragraph}

## Sections
{article['body']}

## Frequently Asked Questions
"""
    return markdown_content

def main():
    st.sidebar.title("Navigation")
    page = st.sidebar.radio("Go to", ["Input Page", "Result Page"])

    if page == "Input Page":
        st.title("Markdown Content Generator")

        if 'example_text' not in st.session_state:
            st.session_state['example_text'] = ""
        if 'keyword' not in st.session_state:
            st.session_state['keyword'] = ""
        if 'competitor_urls' not in st.session_state:
            st.session_state['competitor_urls'] = ""

        example_text = st.text_area("Enter example markdown text:", height=300, value=st.session_state['example_text'])
        keyword = st.text_input("Enter the primary keyword:", value=st.session_state['keyword'])
        competitor_urls = st.text_area("Enter up to 5 competitor URLs, separated by commas:", value=st.session_state['competitor_urls'])

        if st.button("Generate Content"):
            st.session_state['example_text'] = example_text
            st.session_state['keyword'] = keyword
            st.session_state['competitor_urls'] = competitor_urls

            competitor_urls_list = [url.strip() for url in competitor_urls.split(",") if url.strip()]

            competitor_data = []
            for url in competitor_urls_list:
                title, meta_description, body = scrape_url(url)
                competitor_data.append({
                    'url': url,
                    'title': title,
                    'meta_description': meta_description,
                    'body': body
                })

            article_content = generate_title_and_article(example_text, keyword)
            article = {
                'title': article_content.split("\n")[0],  # assuming the title is the first line
                'body': "\n".join(article_content.split("\n")[1:])  # the rest is the body
            }

            custom_tags = generate_custom_tags(article['body'], keyword, competitor_data)
            intro_paragraph = generate_intro_paragraph(article['body'], keyword, competitor_data)
            toc_key_takeaways_faqs = generate_toc_key_takeaways_faqs(article['body'], keyword, competitor_data)

            full_content = assemble_markdown(custom_tags, intro_paragraph, toc_key_takeaways_faqs, article)

            # Store the results individually in the session state
            st.session_state['custom_tags'] = custom_tags
            st.session_state['intro_paragraph'] = intro_paragraph
            st.session_state['toc_key_takeaways_faqs'] = toc_key_takeaways_faqs
            st.session_state['full_content'] = full_content

            st.success("Content generated! Go to the Result Page to see the results.")

    elif page == "Result Page":
        st.title("Generated Full Structured Markdown Content")

        if 'full_content' in st.session_state:
            st.markdown("## Custom Tags")
            st.markdown(st.session_state['custom_tags'])

            st.markdown("## Introduction Paragraph")
            st.markdown(st.session_state['intro_paragraph'])

            st.markdown("## Table of Contents, Key Takeaways, and FAQs")
            st.markdown(st.session_state['toc_key_takeaways_faqs'])

            st.markdown("## Full Content")
            st.markdown(st.session_state['full_content'])

            st.sidebar.download_button(
                label="Download the structured markdown file",
                data=st.session_state['full_content'],
                file_name="structured_content.md",
                mime="text/markdown"
            )
        else:
            st.warning("No content generated yet. Please go to the Input Page to generate content.")

if __name__ == "__main__":
    main()
