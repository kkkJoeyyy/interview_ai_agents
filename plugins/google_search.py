from serpapi import GoogleSearch

API_KEY = "your_serpapi_key"

def google_search(query, num_results=5):
    """使用Google搜索获取结果"""
    search = GoogleSearch({
        "q": query,
        "num": num_results,
        "api_key": API_KEY
    })
    results = search.get_dict()
    return results.get("organic_results", [])