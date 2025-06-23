from aws_cdk import (
    Stack,
    CfnOutput,
    RemovalPolicy,
    aws_cognito as cognito,
    SecretValue,
)
from constructs import Construct
import os
from dotenv import load_dotenv, dotenv_values
from pathlib import Path
import time

class AwscdkStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
                
        # Load environment variables from the shared .env file in root directory
        env_path = Path(__file__).resolve().parent.parent.parent / '.env'
        print(f"Loading environment variables from {env_path}")
        env_vars = dotenv_values(dotenv_path=env_path)

        profile_name = os.environ.get('AWS_PROFILE')
        google_client_id = env_vars.get('GOOGLE_CLIENT_ID')
        google_client_secret = env_vars.get('GOOGLE_CLIENT_SECRET')
        
        
        if not google_client_id or not google_client_secret:
            raise ValueError("GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET environment variables must be set")
        
        callback_urls = [

            "https://tutorial-django-cognito.klaudsol.com/callback",
            "http://localhost:8000/callback",
        ]
        
        logout_urls = [
            "https://tutorial-django-cognito.klaudsol.com/",
            "http://localhost:8000/",
        ]
        
        # Create Cognito User Pool with minimal configuration
        user_pool = cognito.UserPool(
            self, "TutorialDjangoCongitoUserPool",
            user_pool_name="tutorial-django-cognito-user-pool",
            custom_attributes={
                "picture": cognito.StringAttribute(max_len=2048)
            },
        )

        
        # We go L1 since cognito.UserPoolIdentityProviderGoogle
        # does not support the picture attribute.
        google_provider = cognito.CfnUserPoolIdentityProvider(
            self, "TutorialDjangoCognitoGoogleIDP",
            provider_name="Google",
            provider_type="Google",
            user_pool_id=user_pool.user_pool_id,
            provider_details={
                "client_id": google_client_id,
                "client_secret": google_client_secret,
                "authorize_scopes": "openid email profile"
            },
            attribute_mapping={
                "picture": "picture",
                "email": "email",
                "given_name": "given_name",
                "family_name": "family_name",

            }
        )

        # Create User Pool Client with minimal configuration
        user_pool_client = cognito.UserPoolClient(
            self, "TutorialDjangoCognitoUserPoolClient",
            user_pool=user_pool,
            # OAuth configuration for hosted UI
            o_auth=cognito.OAuthSettings(
                flows=cognito.OAuthFlows(
                    authorization_code_grant=True
                ),
                scopes=[
                    cognito.OAuthScope.EMAIL,
                    cognito.OAuthScope.OPENID,
                    cognito.OAuthScope.PROFILE
                ],
                callback_urls=callback_urls,
                logout_urls=logout_urls
            ),
            supported_identity_providers=[
                cognito.UserPoolClientIdentityProvider.GOOGLE
            ]
        )

        # Add dependency to ensure Google provider is created before the client
        user_pool_client.node.add_dependency(google_provider)

        # Create User Pool Domain for hosted UI
        # Note: Looks like the 63 character limit is for the entire domain name.
        # and not the prefix only.
        # If the domain prefix is too long, and  in effect the whole domain name, 
        # CDK will throw an error.
        # https://docs.aws.amazon.com/cognito-user-identity-pools/latest/APIReference/API_CreateUserPoolDomain.html
        domain_prefix = f"tutorialklaudsol"
        user_pool_domain = cognito.UserPoolDomain(
            self, "TutorialDjangoCognitoUserPoolDomain",
            user_pool=user_pool,
            cognito_domain=cognito.CognitoDomainOptions(
                domain_prefix=domain_prefix
            )
        )

        # Use this output as environment variable in our Django app.
        CfnOutput(
            self, "UserPoolId",
            value=user_pool.user_pool_id,
            description="Cognito User Pool ID"
        )

        # Use this output as environment variable in our Django app.
        CfnOutput(
            self, "UserPoolClientId",
            value=user_pool_client.user_pool_client_id,
            description="Cognito User Pool Client ID"
        )

        # Use this output as environment variable in our Django app.
        # The Django app will redirect to this URL to initiate the login process.
        CfnOutput(
            self, "LoginUrl",
            value=f"https://{user_pool_domain.domain_name}.auth.{self.region}.amazoncognito.com/login?client_id={user_pool_client.user_pool_client_id}&response_type=code&scope=email+openid+profile&redirect_uri={callback_urls[0]}",
            description="Direct login URL - use this to test login"
        )

        # Use this URL as Authorized redirect URI in Google
        CfnOutput(
            self, "AuthorizedRedirectURIs",
            value=f"https://{user_pool_domain.domain_name}.auth.{self.region}.amazoncognito.com/oauth2/idpresponse",
            description="Use this URL as Authorized redirect URI in Google"
        )

        # Use this to debug if we set our AWS_PROFILE correctly.
        CfnOutput(
            self, "CurrentProfile",
            value=f"{profile_name}",
            description="AWS Profile being used"
        )

