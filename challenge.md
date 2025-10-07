Technical Test (please specify to users that this is not what we do in production)
Specifications:
**Build a service with Django:**
- **Application should have at least 2 endpoints:**
1. **POST /prompts**: This endpoint should receive a prompt, process it using a language model (you can use any model you prefer), and save both the prompt and the response.
2. **GET /prompts/similar**: This endpoint should receive a prompt and return similar prompts. You can use libraries like FAISS/chroma or any similar solution for this.
- **Application should be built using Python, Django, and DRF** and include proper routing, error handling, and validations.
- **Authentication management**: All endpoints should be protected with token-based authorization. You will need to create a user management system and a route to log in to obtain a token.
- **For POST /prompts**: There should be an option (either through another endpoint or a parameter in the body) to send the response via websocket (you can choose the structure and management for this).
- **Include a README.md file** in your GitHub repository with clear instructions on how to test and check the service.
- **Optional: Provide documentation on how you would deploy this service to AWS.** You can either include terraform scripts or any relevant files that describe the infrastructure setup for AWS. While you don't need to deploy it, we want to know if you have a plan for deployment.
- **Logging and monitoring**: The application should include proper logging and monitoring.
- **Database management**: Use a database like PostgreSQL or MySQL to manage data.
- **Version control**: Use GitHub (or another Git repository). It’s a bonus if you include GitHub Actions for CI/CD, but since the infrastructure won’t be deployed, it's okay if this part fails.
- **Unit tests**: Implement unit tests for at least the endpoints.
- Implement API throttling for POST /prompts, it would be great. Throttling rules: 1 API call per second allowed, 10 API calls per minute.