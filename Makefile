NAME=freko

deploy:
	chalice deploy --no-autogen-policy

policy:
	aws iam get-role-policy --role-name $(NAME) --policy-name $(NAME)
