const fs = require('fs');
const path = require('path');
const DATA_FILE = path.join(__dirname, '../data.json'); 

function readData() {
    const raw = fs.readFileSync(DATA_FILE, 'utf8');
    return JSON.parse(raw).applications;
}

function writeData(applications) {
    fs.writeFileSync(DATA_FILE, JSON.stringify({ applications }, null, 2), 'utf8');
}

function sendSuccess(res ,status , data) {
    res.status(status).json({succress: true, data });
}
function sendError(res , status , message) {
    res.status(status).json({success: false, message });
}

exports.getAllApplications = (req, res) => {
    const { status , sort , page , limit } = req.query;
    let result = readData();

    if (status) {
        result = result.filter((app) => app.status === status);
    }
    if (sort === "date") {
        result = result 
        .slice()
        .sort((a,b) => (a.appliedDate > b.appliedDate ? 1 : -1));
}
    if (page && limit) {
        const pageNum = Number(page);
        const limitNum = Number(limit);
        const start = (pageNum - 1) * limitNum;
        result = result.slice(start, start + limitNum);
    };
sendSuccess(res, 200, result);

}