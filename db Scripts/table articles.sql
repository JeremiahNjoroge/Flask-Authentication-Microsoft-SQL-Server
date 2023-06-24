CREATE TABLE articles(
    id INT IDENTITY(1,1) PRIMARY KEY,
    title VARCHAR(255),
    author VARCHAR(100),
    body TEXT,
    create_date DATETIME DEFAULT GETDATE()
);