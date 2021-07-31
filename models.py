from tortoise import Model, fields


class Guild(Model):
    id = fields.BigIntField(pk=True)

    threads: fields.ReverseRelation["Thread"]

    class Meta:
        table = "guilds"

    def __str__(self) -> str:
        return str(self.id)


class Thread(Model):
    id = fields.BigIntField(pk=True)
    keep_alive = fields.BooleanField(null=False, default=False)
    waiting_on_poll = fields.BooleanField(null=False, default=False)
    guild: fields.ForeignKeyRelation[Guild] = fields.ForeignKeyField(
        "bot.Guild", related_name="threads"
    )

    class Meta:
        table = "threads"

    def __str__(self) -> str:
        return str(self.id)
