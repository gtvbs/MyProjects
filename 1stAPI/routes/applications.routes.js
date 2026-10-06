const express = require('express');
const router = express.Router()

//Get all applications logic
router.get("/", () => {})
//Get applications by stats
router.get("/stats", () => {});
//Get applicaitons by ID
router.get("/:id", () => {});


module.exports = router;

