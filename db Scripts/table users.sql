CREATE TABLE users (
    id INT IDENTITY(1,1) PRIMARY KEY,
    name VARCHAR(100),
    email VARCHAR(100),
    username VARCHAR(30),
    password VARCHAR(100),
    register_date DATETIME DEFAULT GETDATE()
);
