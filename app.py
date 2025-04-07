
### App UI Section ###


import streamlit as st

## Sample data which you source from "enriched_responses" & "references_dict" as prepared above:

import pickle

with open('news_articles_070425_v2.pkl', 'rb') as f:
    interim_news_articles = pickle.load(f)


news_articles=[]
for individual_article in interim_news_articles:
    tag_value=(individual_article['tags'][1:-1].replace('"','').split(','))
    individual_article['tags']=[individual_tag.strip() for individual_tag in tag_value]
    individual_article['date']=individual_article['date'].split('T')[0]
    news_articles.append(individual_article)

  
research_papers= []

### Functional Design
def filter_by_tag(data, selected_tag):
    """Filter a list of items by checking if the selected tag is in their tags list."""
    return [item for item in data if selected_tag in item["tags"]]

def get_all_tags(datasets):
    """Extract a sorted list of unique tags from multiple datasets."""
    tags = set()
    for data in datasets:
        for item in data:
            tags.update(item["tags"])
    return sorted(tags)


### Layout design 
st.title("Climate Risk Insurance Dashboard")

# Sidebar for tag selection
st.sidebar.header("Filter by Tag")
all_tags = get_all_tags([news_articles, research_papers])
selected_tag = st.sidebar.selectbox("Select a tag", all_tags)

# Display filtered News Articles
st.header(f"News Articles Tagged: {selected_tag}")
filtered_news = filter_by_tag(news_articles, selected_tag)
if filtered_news:
    for article in filtered_news:
        st.subheader(article["title"])
        st.caption(f"{article['source']} | {article['date']}")
        st.write(article["summary"])
        st.markdown(f"[news link]({article['url_link']})")
        st.markdown("---")
else:
    st.write("No news articles match this tag.")

### Interactions output Design
st.header(f"Research Papers Tagged: {selected_tag}")
filtered_research = filter_by_tag(research_papers, selected_tag)
if filtered_research:
    for paper in filtered_research:
        st.subheader(paper["title"])
        st.caption(f"{paper['authors']} | {paper['date']}")
        st.write(paper["abstract"])
        st.markdown(f"[research link]({paper['url_link']})")
        st.markdown("---")
else:
    st.write("No research papers match this tag.")

st.sidebar.markdown("### About")
st.sidebar.info(
    "This dashboard integrates news and academic research on climate risk insurance. "
    "Select a tag to see related items from both news and arXiv research."
)





