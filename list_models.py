from google import genai

client = genai.Client(api_key="your_api_key")
for model in client.models.list():
    if "flash" in model.name:
        print(model.name)
