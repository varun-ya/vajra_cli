exports.handler = async (event) => {
    try {
        const { name = 'World', operation = 'greet' } = event;
        const env = process.env.ENVIRONMENT || 'production';
        
        if (operation === 'greet') {
            return {
                message: `Hello ${name} from Node.js!`,
                timestamp: new Date().toISOString(),
                environment: env,
                runtime: 'nodejs18'
            };
        } else if (operation === 'calculate') {
            const { a = 0, b = 0 } = event;
            return {
                operation: 'multiply',
                result: a * b,
                inputs: { a, b }
            };
        } else {
            throw new Error(`Unknown operation: ${operation}`);
        }
    } catch (error) {
        return {
            error: error.message,
            type: error.constructor.name,
            timestamp: new Date().toISOString()
        };
    }
};