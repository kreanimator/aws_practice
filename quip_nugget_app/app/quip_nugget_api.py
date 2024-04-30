from fastapi import FastAPI, HTTPException
from quip_nugget import generate_joke, generate_fact, generate_keywords, validate_input

app = FastAPI()
MAX_INPUT_LENGTH = 32


@app.get("/generate_joke")
async def generate_joke_api(prompt: str):
    if validate_input(prompt):
        joke = generate_joke(prompt)
        return {"joke":     joke,
                "fact":     None,
                "keywords": []}
    else:
        raise HTTPException(status_code=400, detail=f"Invalid input length! Should be no more than {MAX_INPUT_LENGTH}")


@app.get("/generate_fact")
async def generate_fact_api(prompt: str):
    if validate_input(prompt):
        fact = generate_fact(prompt)
        return {"joke":     None,
                "fact":     fact,
                "keywords": []}
    else:
        raise HTTPException(status_code=400, detail=f"Invalid input length! Should be no more than {MAX_INPUT_LENGTH}")


@app.get("/generate_keywords")
async def generate_keywords_api(prompt: str):
    if validate_input(prompt):
        keywords = generate_keywords(prompt)
        return {"joke":     None,
                "fact":     None,
                "keywords": keywords}
    else:
        raise HTTPException(status_code=400, detail=f"Invalid input length! Should be no more than {MAX_INPUT_LENGTH}")


@app.get("/generate_data")
async def generate_data_api(prompt: str):
    if validate_input(prompt):
        joke = generate_joke(prompt)
        fact = generate_fact(prompt)
        keywords = generate_keywords(prompt)
        return {"joke":     joke,
                "fact":     fact,
                "keywords": keywords}
    else:
        raise HTTPException(status_code=400, detail=f"Invalid input length! Should be no more than {MAX_INPUT_LENGTH}")


#   uvicorn quip_nugget_api:app --reload
