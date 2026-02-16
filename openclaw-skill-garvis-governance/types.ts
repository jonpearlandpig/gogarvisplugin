export interface GarvisAuthorityCheckInput {
  user_id: string;
  action: string;
  context?: string;
}

export interface GarvisAuthorityCheckResult {
  approved: boolean;
  reason: string;
  required_role?: string;
}
