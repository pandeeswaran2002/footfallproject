from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List
from datetime import datetime, date
from pymongo import MongoClient
from fastapi.middleware.cors import CORSMiddleware
from fastapi import Query

app = FastAPI()




 
client = MongoClient("mongodb://localhost:27017/")
db = client['footfall']
collection = db['footfall_collection']
summary_collection = db['footfall_summary']  # New collection for summarized data

origins = [
    "http://127.0.0.1:8002",  # Frontend server URL
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class Footfall(BaseModel):
    cameraID: int
    date: datetime
    zone: str
    count: int = 0
    footfalls: List[datetime] = []

class CountToAdd(BaseModel):
    count_to_add: int



@app.post("/footfall/")
async def create_footfall(footfall: Footfall):
    footfall_dict = footfall.dict()
    collection.insert_one(footfall_dict)
    return {"message": "Footfall data created successfully."}

@app.put("/footfall/update/{cameraID}")
async def update_footfall(cameraID: int):
    document = collection.find_one({"cameraID": cameraID})
    if document:
        current_count = document.get("count", 0)
        collection.update_one(
            {"cameraID": cameraID},
            {
                "$set": {"count": current_count + 1},
                "$push": {"footfalls": datetime.now()}
            }
        )
        return {"message": "Count incremented and timestamp added."}
    else:
        raise HTTPException(status_code=404, detail="Document with cameraID not found.")

@app.put("/footfall/add/{cameraID}")
async def add_footfall(cameraID: int, count_data: CountToAdd):
    document = collection.find_one({"cameraID": cameraID})
    if document:
        current_count = document.get("count", 0)
        new_count = current_count + count_data.count_to_add
        new_timestamps = [datetime.now() for _ in range(count_data.count_to_add)]
        collection.update_one(
            {"cameraID": cameraID},
            {
                "$set": {"count": new_count},
                "$push": {"footfalls": {"$each": new_timestamps}}
            }
        )
        return {"message": f"Count updated to {new_count} and {count_data.count_to_add} timestamps added."}
    else:
        raise HTTPException(status_code=404, detail="Document with cameraID not found.")

@app.get("/footfall/")
async def get_all_footfalls():
    footfalls = list(collection.find({}, {"_id": 0}))  
    return footfalls

@app.delete("/footfall/{cameraID}")
async def delete_footfall(cameraID: int):
    result = collection.delete_one({"cameraID": cameraID})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Footfall data not found.")
    return {"message": "Footfall data deleted successfully."}

@app.get("/footfall/count_by_date/")
async def get_count_by_date(query_date: date):
    """
    Retrieve the total count of footfalls added on the specified date.
    """
    # Convert the date to the start and end of the day
    start_datetime = datetime.combine(query_date, datetime.min.time())
    end_datetime = datetime.combine(query_date, datetime.max.time())

    # Find documents where timestamps in `footfalls` fall within the specified date range
    documents = collection.find({
        "footfalls": {
            "$gte": start_datetime,
            "$lt": end_datetime
        }
    })

    # Calculate the total number of timestamps within the date
    total_count = 0
    for document in documents:
        footfalls = document.get('footfalls', [])
        # Count timestamps that fall within the specified date range
        daily_count = sum(start_datetime <= footfall <= end_datetime for footfall in footfalls)
        total_count += daily_count

    return {"date": query_date, "count": total_count}
from fastapi import Query

@app.get("/footfall/count_by_time_range/")
async def get_count_by_time_range(
    query_date: date, 
    start_time: int = Query(..., ge=0, le=23),
    end_time: int = Query(..., ge=0, le=23)
):
    """
    Retrieve the total count of footfalls added between the specified time range on a given date.
    """
    # Convert the date and time range to datetime objects
    start_datetime = datetime.combine(query_date, datetime.min.time()).replace(hour=start_time)
    end_datetime = datetime.combine(query_date, datetime.min.time()).replace(hour=end_time)

    # Ensure the end time is always after the start time
    if end_time <= start_time:
        raise HTTPException(status_code=400, detail="End time must be after start time.")

    # Find documents where timestamps in `footfalls` fall within the specified date and time range
    documents = collection.find({
        "footfalls": {
            "$gte": start_datetime,
            "$lt": end_datetime
        }
    })

    # Calculate the total number of timestamps within the specified time range
    total_count = 0
    for document in documents:
        footfalls = document.get('footfalls', [])
        # Count timestamps that fall within the specified date and time range
        time_range_count = sum(start_datetime <= footfall < end_datetime for footfall in footfalls)
        total_count += time_range_count

    return {"date": query_date, "time_range": f"{start_time}:00-{end_time}:00", "count": total_count}

