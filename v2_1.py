import streamlit as st
from openai import OpenAI
import os 
import json
from pathlib import Path
import requests
from bs4 import BeautifulSoup
import time
# Initialize OpenAI client
api_key = os.getenv('OPENAI_API_KEY')
client = OpenAI(api_key=api_key)

# Function definitions (as provided, unaltered)
def scrape_url(url):
    response = requests.get(url)
    if response.status_code != 200:
        return 'No title found', 'No meta description found', 'No body content found'
    soup = BeautifulSoup(response.text, 'html.parser')
    title = soup.find('title').text if soup.find('title') else 'No title found'
    meta_description = soup.find('meta', attrs={'name': 'description'})
    meta_description = meta_description['content'] if meta_description else 'No meta description found'
    body = soup.get_text(separator='\n') if soup.body else 'No body content found'
    return title, meta_description, body.replace('\n','')[:1500]

def create_custom_tags(results, example_content):
    system_prompt = f"""
    You are an expert article editor.
    Your task is to use the results and information from 5 websites given by the user to return the following to the user for the newly created article. 
    Based on findings create custom tags at the top of content, such as title, meta description, article schema.
    We will also give you a sample markdown file in the format the user wants. You have to give us a sample output using this information.
    This is a very important task, so you must definitely fulfill the tasks given to you.
    This is a task where you have no chance of making mistakes, so please do not rush and use all the time you need.

    5 other website Result: {results}

    Example Content format: {example_content}

    You need to thoroughly understand the Example format given to you. I want you to return me a: custom tags at the top of content, such as title, meta description, article schema. using the sample format.
    
    You need to return all of this information you created in JSON format. I want you to create a suitable format and always return it in this format.
    """

    response = client.chat.completions.create(
        model="gpt-4o",
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": "Based on findings create custom tags at the top of content, such as title, meta description, article schema"},
        ]
    )
    return json.loads(response.choices[0].message.content)

def intro_paragraph(custom_tags, my_content, keyword):
    system_prompt = f"""
    You are an expert article writer.
    Your job is to thoroughly review the article I created and then create an introductory paragraph using information from other websites.
    You will be given a keyword and I want you to create a very well-written introductory paragraph using the article I created and information from sample websites.
    This is a very important task and you should never make mistakes. So never rush through this process and you can be as slow as you want.

    Custom tags: {custom_tags},

    My Content: {my_content},

    Keyword: {keyword}
    """
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": "You have to create an introduction paragraph for me using all the information given to you."},
        ]
    )
    return response.choices[0].message.content

def implement_contents(intro_paragraph, custom_tags, keyword, my_content, example_format):
    system_prompt = f"""
    Your task is to create the content in the appropriate format and order.
    In this task, you will be given all the necessary information, you just have to use it in the appropriate format and correctly.

    We created an introductory paragraph using the text written by the user and his information. Here, you have to use the introductory paragraph in the correct format.

    At the same time, the user himself gave us a keyword information, in short, you can think of it as a keyword theme.

    By scanning the 5 sample sites we received from the user, a lot of information from those sites will be given to you at the same time. This information will be very useful for you for sample content.

    Finally, I will give you a sample document for which format you should output. You need to examine this markdown file very, very well and understand its format very well. Because you can only output to the user in this format. You cannot output in any other format.

    You absolutely have to complete these tasks given to you without any errors. Therefore, never rush and never make mistakes.

    Keyword: {keyword},

    Intro Paragraph: {intro_paragraph},

    Custom Tags: {custom_tags},

    User Content: {my_content},

    Example Format you follow the structure: {example_format}
    """
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": "implement table of contents, key takeaways and faqs using the same html formatting as the examples markdown files."},
        ]
    )
    return response.choices[0].message.content

def final_structured(final_format, example_format):
    current_time = time.localtime()
    current_date = time.strftime("%Y-%m-%d", current_time)

    system_prompt = f"""
    Your job is to provide formatting order.
    There is a markdown text that we created for the user and at the same time the user gave us a markdown file with a sample format. By looking at the format of this sample file, you need to ensure that the newly created markdown value has the same structure as the sample markdown text and be 100% sure.

    First of all, you need to examine the markdown text that we created for the user given to you.
    For the second step, you need to examine and understand the markdown file that we gave for the sample format.
    As the third and last step, make sure that the two values ​​have the same format, if you think they are different, edit the value we created for the user in the appropriate format.
    Here, do not ever, ever mix the content of the sample markdown with the content of the markdown value generated for the user.
    You only have to look at the structure and compare.
    1. author tag at top of article should always just be 'Tom & Jess'.
    Use updated Date in structure: {current_date}

    Don't change the article structure too much.
    You can never, ever make a mistake in this regard. Please do not rush. Spend all the time you need.
    Don't leave any comment or You can not add let's start or something like that. Just Return Markdown Text and That's all. Just Return Markdown Text and That's all. Just Return Markdown Text and That's all. 

    User Markdown Text: {final_format},

    Example structure format markdown: {example_format}
    """
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": "Verify that the markdown text I created for the user is in the correct format with the sample markdown text I gave. If there is an error in the structure, correct it."},
        ]
    )
    return response.choices[0].message.content




def main():
    # st.set_page_config(page_title="Custom Article Generator", layout="centered")

    # Sidebar with page selection
    page = st.sidebar.selectbox("Select a page", ["Main Page", "Result Page", "ChatAI"])

    if page == "Main Page":
        st.title("Custom Article Generator")

        # User inputs
        with open('20240611-190000_best-boiler-installers-uk (1).md', 'r') as file:
            example_markdown = file.read()
        
        user_markdown = st.text_area("Your Article Markdown Content", height=200)
        keyword = st.text_input("Primary Keyword")
        urls = st.text_area("Competitor URLs (one per line)").split('\n')

        if st.button("Generate Article"):
            results = {}

            for url in urls:
                title, meta_description, body = scrape_url(url)
                results[url] = {
                    'title': title,
                    'meta_description': meta_description,
                    'body': body
                }

            run2 = create_custom_tags(results, example_markdown)
            run3 = intro_paragraph(run2, user_markdown, keyword)
            run4 = implement_contents(run3, run2, keyword, user_markdown, example_markdown)
            final_result = final_structured(run4, example_markdown)

            st.session_state['final_result'] = final_result

    elif page == "Result Page":
        st.title("Result Page")
        if 'final_result' in st.session_state:
            st.markdown("### Generated Article")
            st.markdown(st.session_state['final_result'])

            # Adding download button for the markdown file
            st.download_button(
                label="Download Markdown",
                data=st.session_state['final_result'],
                file_name='generated_article.md',
                mime='text/markdown'
            )
        else:
            st.markdown("### No article generated yet.")

    elif page == "ChatAI":
        st.title("ChatAI")
        if 'final_result' in st.session_state:
            st.markdown("### Generated Article")
            # st.markdown(st.session_state['final_result'])

            # ChatAI interface
            # client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

            if "openai_model" not in st.session_state:
                st.session_state["openai_model"] = "gpt-4o"

            if "messages" not in st.session_state:
                st.session_state.messages = []

            for message in st.session_state.messages:
                with st.chat_message(message["role"]):
                    st.markdown(message["content"])

            if 'system_info' not in st.session_state:
                st.session_state.messages.append({"role": "system", "content": st.session_state['final_result']})
                

            if prompt := st.chat_input("What is up?"):
                st.session_state.messages.append({"role": "user", "content": prompt})
                with st.chat_message("user"):
                    st.markdown(prompt)

                with st.chat_message("assistant"):
                    stream = client.chat.completions.create(
                        model=st.session_state["openai_model"],
                        messages=[
                            {"role": m["role"], "content": m["content"]}
                            for m in st.session_state.messages
                        ],
                        stream=True,
                    )
                    response = st.write_stream(stream)
                st.session_state.messages.append({"role": "assistant", "content": response})
        else:
            st.markdown("### No article generated yet.")

if __name__ == "__main__":
    main()