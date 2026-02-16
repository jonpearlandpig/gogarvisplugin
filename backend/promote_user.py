import os
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient

MONGO_URL = os.environ.get("MONGO_URL")
DB_NAME = os.environ.get("DB_NAME")

async def promote_user(email: str, role: str = "admin"):
    client = AsyncIOMotorClient(MONGO_URL)
    db = client[DB_NAME]
    result = await db.users.update_one({"email": email}, {"$set": {"role": role}})
    if result.matched_count:
        print(f"Promoted {email} to {role}.")
    else:
        print(f"User {email} not found.")
    client.close()

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python promote_user.py <email> [role]")
        exit(1)
    email = sys.argv[1]
    role = sys.argv[2] if len(sys.argv) > 2 else "admin"
    asyncio.run(promote_user(email, role))
