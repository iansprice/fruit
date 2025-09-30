# Fruit

This project is a full stack application that helps a secret fruit-based mission-driven company.

## Stack

DB: Postgres17
Backend: Flask
Frontend: React + Tailwind

## Development

The Flask app here serves the `frontend/build` dir (the output of `npm run build`).
When updating the front-end, run this command to update the files served.

### `npm run build`

Builds the app for production to the `build` folder.\
It correctly bundles React in production mode and optimizes the build for the best performance.

The build is minified and the filenames include the hashes.\
Your app is ready to be deployed!

See the section about [deployment](https://facebook.github.io/create-react-app/docs/deployment) for more information.

### Deployment

This application is currently deployed on GCP. 
A tiny VM and minimally resourced PostgreSQL server power the application. 
To maximize performance we are performing aggregation/calculations directly in PostgreSQL.

### Contact

ian@redmountainsoftware.com