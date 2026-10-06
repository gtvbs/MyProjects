const express  = require('express');
const applicationRouter = require('./routes/applications.routes');
const app = express();

app.use(express.json());
app.use((req, res, next) => {
    console.log(`${req.method} ${req.url}`);
    next();
});

app.get('/', (req, res) => {
    res.send('Welcome to the Job tracker API');
});
app.use('/applications', applicationRouter);

app.use((req, res) => {
    res.status(404).send('Route not found');
});

app.use((err, req, res, next) => {
    console.error(err.stack);
    res.status(500).send('Internal Server Error');
});
app.listen(3000, () => {
    console.log('Job tracker API is running on http://localhost:3000');
}); 

