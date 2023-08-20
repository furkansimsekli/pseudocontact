import aiosqlite


class ContactDatabase:
    def __init__(self, db_path="./database.sqlite"):
        self.connection = None
        self.db_path = db_path

    async def connect(self):
        self.connection = await aiosqlite.connect(self.db_path)
        await self.create_table()

    async def disconnect(self):
        await self.connection.close()

    async def create_table(self):
        await self.connection.execute(
            """
            CREATE TABLE IF NOT EXISTS contacts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                owner INTEGER NOT NULL,
                name TEXT NOT NULL,
                number TEXT NOT NULL
            )
            """
        )
        await self.connection.commit()

    async def add_new(self, owner, name, number):
        await self.connection.execute(
            "INSERT INTO contacts (owner, name, number) VALUES (?, ?, ?)",
            (owner, name, number)
        )
        await self.connection.commit()

    async def all(self, owner):
        async with self.connection.execute(
                "SELECT * FROM contacts WHERE owner LIKE ?",
                (f"%{owner}",)
        ) as cursor:
            rows = await cursor.fetchall()

        return rows

    async def find(self, owner, search_term):
        async with self.connection.execute(
                "SELECT * FROM contacts WHERE owner LIKE ? AND name LIKE ? OR number LIKE ?",
                (f"%{owner}", f"%{search_term}%", f"%{search_term}%")
        ) as cursor:
            rows = await cursor.fetchall()

        return rows
