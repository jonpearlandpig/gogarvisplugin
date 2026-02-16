import { tools, hooks, SkillContext } from 'openclaw';
import { GarvisAuthorityCheckInput, GarvisAuthorityCheckResult } from './types';
import { getMongoClient } from './mongo';

const MONGODB_URI = process.env.MONGODB_URI || '';
const DB_NAME = 'garvis_governance';

async function authorityCheck(
  input: GarvisAuthorityCheckInput,
  context: SkillContext
): Promise<GarvisAuthorityCheckResult> {
  const client = await getMongoClient(MONGODB_URI);
  const db = client.db(DB_NAME);

  let approved = false;
  let required_role = '';
  let reason = '';
  try {
    const roles = db.collection('roles');
    const user = await roles.findOne({ user_id: input.user_id });
    // Example: action-to-role mapping
    const actionRoleMap: Record<string, string> = {
      'delete_file': 'admin',
      'openai_call': 'analyst',
      // ...add more
    };
    required_role = actionRoleMap[input.action] || 'user';
    if (user && user.roles && user.roles.includes(required_role)) {
      approved = true;
      reason = 'User has required role';
    } else {
      approved = false;
      reason = `Missing required role: ${required_role}`;
    }
  } catch (err) {
    approved = false;
    reason = 'Error during authority check: ' + (err as Error).message;
  }

  // Audit log
  try {
    const audit = db.collection('audit_log');
    await audit.insertOne({
      timestamp: new Date(),
      user_id: input.user_id,
      action: input.action,
      context: input.context || null,
      approved,
      reason,
      required_role,
    });
  } catch (err) {
    // Optionally log audit failure elsewhere
  }

  return { approved, reason, required_role };
}

// Register the tool
tools.register({
  name: 'garvis_authority_check',
  description: 'Checks if a user is authorized to perform an action according to GARVIS governance.',
  inputSchema: {
    user_id: 'string',
    action: 'string',
    context: { type: 'string', optional: true },
  },
  outputSchema: {
    approved: 'boolean',
    reason: 'string',
    required_role: { type: 'string', optional: true },
  },
  run: authorityCheck,
});

// Optional: Pre-LLM hook to enforce governance
hooks.onPreLLM(async (msg, context) => {
  const user_id = context.user?.id || 'unknown';
  const action = 'openai_call';
  const result = await authorityCheck({ user_id, action }, context);
  if (!result.approved) {
    throw new Error(`GARVIS Governance: ${result.reason}`);
  }
});
