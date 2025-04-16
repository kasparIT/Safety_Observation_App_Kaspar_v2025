!/bin/bash

RESOURCE_GROUP="SafetyApplicationApp_Revamp"
APP_NAME="KasparSafetyObs"

echo "Applying IP Access Restrictions to $APP_NAME in $RESOURCE_GROUP..."

declare -A ip_map=(
["198.46.13.210"]="KCI GVEC Fiber Network"
["104.15.128.85"]="KCI ATT Backup Fiber Network"
["12.27.153.10"]="Allow_Default_01"
["66.76.242.17"]="Allow_Default_02"
["12.179.157.74"]="Allow_Default_03"
["216.45.94.26"]="Allow_Default_04"
["12.175.195.250"]="Allow_Default_05"
["12.175.194.34"]="Allow_Default_06"
["216.177.178.146"]="Allow_Default_07"
["12.32.159.58"]="Allow_Default_08"
["12.34.235.106"]="Allow_Default_09"
["12.28.64.26"]="Allow_Default_10"
["216.82.155.148"]="Allow_Default_11"
["12.239.99.146"]="Allow_Default_12"
["216.82.139.167"]="Allow_Default_13"
["216.82.139.138"]="Allow_Default_14"
["216.82.139.147"]="Allow_Default_15"
["12.230.159.242"]="Allow_Default_16"
["69.146.89.98"]="Allow_Joey_01"
["76.30.110.158"]="Allow_Joey_02"
["98.200.120.173"]="Allow_Joey_03"
["108.213.191.135"]="Allow_Meagan"
["72.182.221.127"]="Allow_Remote_01"
["99.30.244.119"]="Allow_Remote_02"
["107.77.219.50"]="Allow_Remote_03"
["173.173.242.73"]="Allow_Remote_04"
["71.135.64.39"]="Allow_Remote_05"
["74.192.209.79"]="Allow_Remote_06"
["216.82.142.58"]="Allow_Remote_07"
["216.82.139.237"]="Allow_Remote_08"
["76.187.194.104"]="Allow_Remote_09"
["47.221.201.184"]="Allow_Remote_10"
["50.84.153.198"]="Allow_Remote_11"
["70.112.38.130"]="Allow_Remote_12"
["69.145.144.227"]="Allow_Remote_13"
["75.108.22.61"]="Allow_Remote_14"
["69.5.215.154"]="Allow_Remote_15"
["190.11.85.243"]="Allow_Remote_16"
["189.28.83.130"]="Allow_Remote_17"
["189.28.83.62"]="Allow_Remote_18"
["189.28.83.204"]="Allow_Remote_19"
["189.28.83.111"]="Allow_Remote_20"
["189.28.83.30"]="Allow_Remote_21"
["189.28.83.113"]="Allow_Remote_22"
["189.28.81.158"]="Allow_Remote_23"
["189.28.83.128"]="Allow_Remote_24"
["189.28.83.22"]="Allow_Remote_25"
["189.28.83.53"]="Allow_Remote_26"
["136.49.105.152"]="Allow_Ariel_01"
["104.14.191.119"]="Allow_Ariel_02"
["45.84.120.228"]="Allow_TPM_NordLayer"
["198.46.13.211"]="Allow_TPM_GVEC"
["209.215.19.67"]="Allow_TPM_ATT_01"
["209.215.19.97"]="Allow_TPM_ATT_02"
["75.109.214.169"]="Allow_Horizon_01"
["75.109.214.163"]="Allow_Horizon_02"
["69.5.194.74"]="Allow_Horizon_03"
["71.42.81.58"]="Allow_CircleY_01"
["71.42.81.59"]="Allow_CircleY_02"
["71.42.81.60"]="Allow_CircleY_03"
["70.118.93.62"]="Allow_PST"
["146.70.58.234"]="Allow_ShaiHerman"
["73.45.190.162"]="Allow_JonFretz"
["104.254.220.119"]="Allow_JerryCourtney"
["64.250.12.199"]="Allow_ChrisTaggart"
["166.198.198.140"]="Allow_DaraLoudon"
["174.128.236.75"]="Allow_TedKraus"
["98.97.90.85"]="Allow_TPM_Generic"
["132.147.145.194"]="Allow_DyanaGracey"
["71.12.153.130"]="Allow_ScottFine"
["38.67.53.220"]="Allow_CaitlinElston"
["96.18.93.93"]="Allow_CandaceLantiegne"
["73.166.115.178"]="Allow_ArielGherman"
)

priority=100

for ip in "${!ip_map[@]}"; do
  name=${ip_map[$ip]}
  echo "Adding $ip ($name) with priority $priority..."
  az webapp config access-restriction add \
    --resource-group "$RESOURCE_GROUP" \
    --name "$APP_NAME" \
    --rule-name "$name" \
    --priority $priority \
    --action Allow \
    --ip-address "$ip/32"
  ((priority++))
done

echo "Adding final DenyAll fallback rule..."
az webapp config access-restriction add \
  --resource-group "$RESOURCE_GROUP" \
  --name "$APP_NAME" \
  --rule-name "DenyAll" \
  --priority 999 \
  --action Deny \
  --ip-address "0.0.0.0/0"

echo "✅ All rules applied successfully."
