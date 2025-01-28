import secrets

# Generate SECRET_KEY
secret_key = secrets.token_hex(32)
print("\nSECRET_KEY:")
print(secret_key)

# Generate JWT_SECRET_KEY
jwt_secret_key = secrets.token_hex(32)
print("\nJWT_SECRET_KEY:")
print(jwt_secret_key) 