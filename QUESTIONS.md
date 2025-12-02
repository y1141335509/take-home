Assignment
Data Engineer Assignment
Please use this simple assignment to demonstrate your proficiency in Python, defining a database schema, writing clear and succinct documentation, and time management skills.



Assignment Overview
You are tasked with writing a Python application that extracts data from a public third-party API, performs some transformations, loads the cleaned data into a local instance of a PostgreSQL database, and finally reads some interesting subset of the data.



Deliverables
A Python file containing the complete ETL logic.

A README file explaining how to set up the environment, run the script, and any choices you have made such as the database schema.

Any other files needed to showcase your solution

You are strongly encouraged to use AI tools to improve productivity. Please also include any AI prompts and tools you used in the README.

Keep it simple
You are encouraged to keep the problem simple in the interest of time. It is more important to have clearly communicated and succinct documentation than to have complex or fully complete code.

AI tools are strongly encouraged: You are strongly encouraged to use AI tools to write code and improve your productivity. Please include some prompts and which AI tool you used in the write up.

Feel free to skip steps: If there is a step in the process that may require too much setup or code to actually complete, feel free to skip it or mock it. If there are best practices for security or devops that you have skipped in the interest of time be sure to discuss how it should be done given more time. Please mention any skipped steps in the write up with an explanation on what the step should do and why it was skipped.

Feel free to think outside the box: On the other hand, if there are important things you think should be included or skills you would like to highlight such as ability to formulate efficient join statements or things that you think are particularly relevant to GridCARE’s mission please add them in with a discussion in the README.

Try not to spend more than 3 hours: If it will take you more than 3 hours to complete this task then you may have picked too complex of a problem. Feel free to skip or mock some steps and take advantage of AI to generate boilerplate code and documentation.

Requirements
1. Data
Source: Choose any freely available third-party API that provides data (e.g., public APIs for weather, finance, books, or open data government sources). If you want to use an interesting data source that does not have a public API please include some samples of the data and a discussion on where and how you found it and why you think its interesting.

2. Transformation
Keep it simple: Please do not spend much time on complex or complete transformation logic. It is more important to write clear and succinct documentation than to have fully complete code.

Feature Engineering/Selection: Select a subset of the extracted fields, and create at least one new computed column based on existing data.

3. Loading
Destination: PostgreSQL database. Feel free to use docker to setup and contain the database.

Tools: Use the psycopg2 or SQLAlchemy library for database interaction.

Schema Definition: The script must dynamically create the target table if it does not already exist.

4. Querying
Verify data was saved: By writing a function to query the database and return some interesting subset of the data.

Tips
Google Gemini is a free AI tool you can use that requires no account or any prior setup. Feel free to use whatever tool you prefer. https://gemini.google.com/app

You could have your AI tool solve the entire homework by simply sending it this assignment and asking it to do so. However, the choice of API it picks, feature engineering, schema definition, and final query may not be particularly interesting or relevant for GridCARE’s specific use cases. Additionally, the AI may not include best practices for security, DevOps, code readability and scalability. Please keep this in mind to help distinguish your answer from a generic AI solution. We would like to see good contextual judgement in combination with AI for productivity.

Submission
Please submit your work within 72 hours of receiving the assignment excluding Saturday and Sunday. The submission should contain your Python script, the README file, and any other files.


Please email any questions to thomas@gridcare.ai.