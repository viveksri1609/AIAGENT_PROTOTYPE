## AI App Prototype Using FASTAPI Ollama + Llama 3

This application runs locally using **Ollama**.

Download Ollama: https://ollama.com

## Start the server
```bash
ollama serve
```
The app uses the **Llama 3** model from Meta.

Open a new terminal and run the model
## Run the Model


```bash
ollama run llama3
```

Open a new terminal and run the uvicorn server

## Run Uvicorn 
```bash
 uvicorn main:app --reload
```

