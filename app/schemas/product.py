from marshmallow import Schema, fields, validate


class ProductCreateSchema(Schema):
    """Schema for product creation requests."""
    name = fields.String(required=True, validate=validate.Length(min=1, max=255))
    description = fields.String(required=False, allow_none=True)
    price = fields.Decimal(required=True, as_string=True, validate=validate.Range(min=0.01))
    stock = fields.Integer(required=True, validate=validate.Range(min=0))


class ProductPatchSchema(Schema):
    """Schema for partial product update requests."""
    name = fields.String(required=False, validate=validate.Length(min=1, max=255))
    description = fields.String(required=False, allow_none=True)
    price = fields.Decimal(required=False, as_string=True, validate=validate.Range(min=0.01))
    stock = fields.Integer(required=False, validate=validate.Range(min=0))
