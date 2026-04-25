from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
import io

app = FastAPI(title="Provision Shop Sales API")
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:4200"], allow_methods=["*"], allow_headers=["*"])

# In-memory session storage
session = {"raw_data": None, "cleaned_data": None, "mode": None, "analysis_triggered": False}

def parse_delimited(content: str, delimiter: str) -> pd.DataFrame:
    df = pd.read_csv(io.StringIO(content), delimiter=delimiter, header=None, names=["period", "sales"])
    df["sales"] = pd.to_numeric(df["sales"], errors="coerce")
    return df.dropna().drop_duplicates().reset_index(drop=True)

@app.post("/upload")
async def upload(file: UploadFile = File(...), delimiter: str = ","):
    content = await file.read()
    df = parse_delimited(content.decode("utf-8"), delimiter)
    session["raw_data"] = df.to_dict(orient="records")
    return {"status": "uploaded", "rows": len(df)}

@app.post("/clean")
async def clean_data():
    if not session["raw_data"]:
        raise HTTPException(400, "No raw data uploaded")
    df = pd.DataFrame(session["raw_data"])
    # Clean: clip negative sales, sort logically
    df["sales"] = df["sales"].clip(lower=0)
    session["cleaned_data"] = df.to_dict(orient="records")
    session["analysis_triggered"] = False
    return {"status": "cleaned", "data": session["cleaned_data"]}

@app.post("/upload-cleaned")
async def upload_cleaned(file: UploadFile = File(...), delimiter: str = ","):
    content = await file.read()
    df = parse_delimited(content.decode("utf-8"), delimiter)
    df["sales"] = df["sales"].clip(lower=0)
    session["cleaned_data"] = df.to_dict(orient="records")
    return {"status": "cleaned_override", "rows": len(df)}

@app.post("/graph")
async def get_graph_data():
    if not session["cleaned_data"]:
        raise HTTPException(400, "No cleaned data available")
    return {"labels": [r["period"] for r in session["cleaned_data"]], 
            "values": [r["sales"] for r in session["cleaned_data"]]}

@app.post("/analyze/{type}")
async def analyze(type: str):
    if not session["cleaned_data"]:
        raise HTTPException(400, "No cleaned data")
    session["analysis_triggered"] = True
    df = pd.DataFrame(session["cleaned_data"])
    if type == "summary":
        return {"total": float(df["sales"].sum()), "avg": float(df["sales"].mean()), "max": float(df["sales"].max())}
    elif type == "table":
        return {"data": session["cleaned_data"]}
    elif type == "chart":
        return {"labels": list(df["period"]), "values": list(df["sales"])}
    return {}

@app.post("/predict")
async def predict():
    if not session["cleaned_data"]:
        raise HTTPException(400, "No cleaned data")
    df = pd.DataFrame(session["cleaned_data"])
    X = np.arange(len(df)).reshape(-1, 1)
    y = df["sales"].values
    model = LinearRegression().fit(X, y)
    
    # Predict next 3 periods
    future_idx = np.arange(len(df), len(df) + 3).reshape(-1, 1)
    preds = [round(p, 2) for p in model.predict(future_idx)]
    slope = model.coef_[0]
    
    if slope > 50:
        trend, recs = "📈 Increasing", ["Increase inventory stock for upcoming periods.", "Negotiate bulk supplier discounts."]
    elif slope < -50:
        trend, recs = "📉 Decreasing", ["Launch targeted promotions or loyalty discounts.", "Review pricing strategy and product mix."]
    else:
        trend, recs = "➡️ Stable", ["Maintain current inventory levels.", "Focus on customer retention & service quality."]
        
    return {"trend": trend, "predictions": preds, "recommendations": recs}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
