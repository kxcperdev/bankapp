def success_response(data: dict, message: str = "Operation successful"):
    return {
        "status": "success",
        "message": message,
        "data": data
    }

def error_response(message: str, code: int):
    return {
        "status": "error",
        "message": message,
        "code": code
    }
