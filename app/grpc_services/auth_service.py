from app.proto.auth_pb2 import LoginRequest, LoginResponse
from app.proto.auth_pb2_grpc import AuthServiceBase
from app.db.mongodb import get_user_by_login

class AuthService(AuthServiceBase):
    async def Login(self, stream):
        request: LoginRequest = await stream.recv_message()
        user = get_user_by_login(request.login)
        
        if user and user['password'] == request.password:
            response = LoginResponse(
                success=True,
                message="Login successful",
                user_id=str(user["_id"]),
                first_name=user["first_name"],
                last_name=user["last_name"],
                group=user["group"]
            )
        else:
            response = LoginResponse(
                success=False,
                message="Invalid login or password"
            )
        
        await stream.send_message(response)