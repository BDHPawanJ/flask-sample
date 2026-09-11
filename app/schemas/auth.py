from marshmallow import Schema, fields, validate


class RegisterRequestSchema(Schema):
    """Schema for user registration requests."""
    email = fields.Email(required=True)
    password = fields.String(
        required=True,
        load_only=True,
        validate=validate.Length(min=8, max=128),
    )


class LoginRequestSchema(Schema):
    """Schema for user login requests."""
    email = fields.Email(required=True)
    password = fields.String(required=True, load_only=True)
