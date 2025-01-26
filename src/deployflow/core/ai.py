from deployflow import config

_client = None


def get_ai():
    global _client
    if _client:
        return _client
    api_key = config.get_val("ai", "api_key")
    endpoint = config.get_val("ai", "endpoint")
    if not api_key:
        print("AI Services require an API key.")
        endpoint = input("Enter the AI API endpoint: (https://api.deepseek.com) ")
        api_key = input("Enter the API key: ")
        if not endpoint: endpoint = "https://api.deepseek.com"
        if not api_key:
            raise ValueError("API key is required.")
        config.set_val("ai", "api_key", api_key)
        config.set_val("ai", "endpoint", endpoint)

    from openai import OpenAI
    _client = OpenAI(api_key=api_key, base_url=endpoint)
    return _client
