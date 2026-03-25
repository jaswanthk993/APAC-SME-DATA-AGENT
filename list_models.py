from google import genai

client = genai.Client(api_key="AIzaSyAwFptJnUcpkfcDsr0Z1qi-0Uw_QXOcqdk")
for model in client.models.list():
    if "flash" in model.name:
        print(model.name)
