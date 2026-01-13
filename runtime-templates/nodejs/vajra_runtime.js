const express = require('express');
const { Logging } = require('@google-cloud/logging');
const fs = require('fs');
const path = require('path');

const app = express();
app.use(express.json());

// Initialize logging
const logging = new Logging();
const logger = logging.log('vajra-function');

let userFunction = null;

// Load user function
function loadUserFunction() {
    try {
        const handler = process.env.FUNCTION_TARGET || 'handler';
        const mainPath = path.join(__dirname, 'index.js');
        
        if (fs.existsSync(mainPath)) {
            delete require.cache[require.resolve('./index.js')];
            const mainModule = require('./index.js');
            
            if (typeof mainModule[handler] === 'function') {
                userFunction = mainModule[handler];
                logger.info('Function loaded successfully');
            } else {
                throw new Error(`Handler '${handler}' not found in index.js`);
            }
        } else {
            throw new Error('index.js not found');
        }
    } catch (error) {
        logger.error(`Failed to load function: ${error.message}`);
        throw error;
    }
}

// Load function at startup
try {
    loadUserFunction();
} catch (error) {
    console.error('Startup failed:', error.message);
}

app.all('/', async (req, res) => {
    if (!userFunction) {
        return res.status(500).json({ error: 'Function not loaded' });
    }
    
    const startTime = Date.now();
    
    try {
        // Get request data
        const data = req.method === 'POST' ? req.body : req.query;
        
        // Log invocation
        logger.info('Function invoked', {
            method: req.method,
            payloadSize: JSON.stringify(data).length
        });
        
        // Execute user function
        const result = await userFunction(data);
        
        const executionTime = Date.now() - startTime;
        
        // Log success
        logger.info('Function executed successfully', {
            executionTimeMs: executionTime
        });
        
        res.json({
            result: result,
            executionTime: `${executionTime}ms`
        });
        
    } catch (error) {
        const executionTime = Date.now() - startTime;
        
        // Log error
        logger.error('Function execution failed', {
            error: error.message,
            executionTimeMs: executionTime,
            stack: error.stack
        });
        
        res.status(500).json({
            error: error.message,
            executionTime: `${executionTime}ms`
        });
    }
});

app.get('/health', (req, res) => {
    res.json({
        status: 'healthy',
        functionLoaded: userFunction !== null
    });
});

const port = process.env.PORT || 8080;
app.listen(port, '0.0.0.0', () => {
    console.log(`Vajra Node.js runtime listening on port ${port}`);
});