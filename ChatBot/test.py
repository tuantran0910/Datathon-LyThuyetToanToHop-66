from langchain.agents import initialize_agent
from langchain.llms import OpenAI
from langchain.output_parsers import ResponseSchema, StructuredOutputParser
from langchain.prompts import PromptTemplate


def active_func(query):
    response_schemas = [
        ResponseSchema(name="answer",
                       description="name of function with required or similar means to user's input"),
        # ResponseSchema(name="signal",
        #                 description="signal base on description, should be yes or no.")
    ]
    output_parser = StructuredOutputParser.from_response_schemas(
        response_schemas)
    form = """
                "Given the following user input and a list of functions, identify the function associated with the provided input:

                User Input: [{question}]

                List of Functions:
                1. Description: Refuse to answer the question not related to any function.
                Function: refuseToAnswer

                2. Description: Instructions for uploading photos including personal photos and full-body shots.
                Function: uploadPose

                3. Description: Recommend cloth items in database based on user's input.
                Function: recommendCloth

                4. Description: Try or fit or make someone look like in i-th cloth item in user's input.
                Function: tryCloth

                Which function is most closely associated with the provided user input? Choose the corresponding function name from the list."
                {format_instructions}
            """
    format_instructions = output_parser.get_format_instructions()
    prompt = PromptTemplate(
        input_variables=["question"],
        template="Answer the following questions as best you can." + form +
        "If you do not know the answer, then return function name: refuseToAnswer.",
        partial_variables={"format_instructions": format_instructions}
    )

    model = OpenAI(temperature=0)
    _input = prompt.format_prompt(question=query)
    output = model(_input.to_string())

    result = output_parser.parse(output)
    return result


if __name__ == "__main__":
    while True:
        inp = input("Input: ")
        result = active_func(inp)
        print(result)
