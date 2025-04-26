document.addEventListener('DOMContentLoaded', function () {
    initializeSidebar();
  
    if (document.getElementById('savingsHistoryTable')) {
      updateMemberDashboard();
    } else if (document.getElementById('totalMembers')) {
      initializeMembersPage();
    } else {
      updateDashboardData();
    }
});
  
// ========== Sidebar Handling ==========
function initializeSidebar() {
  const sidebarToggler = document.querySelector('.sidebar-toggler');
  const sidebar = document.getElementById('sidebar');
  const overlay = document.createElement('div');
  overlay.className = 'sidebar-overlay';
  document.body.appendChild(overlay);

  function toggleSidebar() {
    if (window.innerWidth < 992) {
      sidebar.classList.toggle('show');
      overlay.classList.toggle('show');
    }
  }

  sidebarToggler.addEventListener('click', toggleSidebar);
  overlay.addEventListener('click', toggleSidebar);

  window.addEventListener('resize', function () {
    if (window.innerWidth >= 992) {
      sidebar.classList.remove('show');
      overlay.classList.remove('show');
    }
  });

  const navLinks = sidebar.querySelectorAll('.nav-link');
  navLinks.forEach(link => {
    link.addEventListener('click', function () {
      if (window.innerWidth < 992) toggleSidebar();
      navLinks.forEach(l => l.classList.remove('active'));
      this.classList.add('active');
    });
  });
}
  
// ========== Dashboard Overview ==========
function updateDashboardData() {
  const dashboardData = window.dashboardData || {
    total_group_savings: 0,
    totalInvested: 0,
    uninvested: 0,
    interestGained: 0,
    investment_pools: []
  };

  const totalGroupSavingsEl = document.getElementById('totalGroupSavings');
  if (totalGroupSavingsEl) {
    totalGroupSavingsEl.textContent = formatCurrency(dashboardData.total_group_savings);
  }

  updateElement('totalInvested', formatCurrency(dashboardData.totalInvested));
  updateElement('uninvestedAmount', formatCurrency(dashboardData.uninvested));
  updateElement('interestGained', formatCurrency(dashboardData.interestGained));

  updateInvestmentPools();
  updateWeeklySavings();
  updateMembersOverview();
}

function updateInvestmentPools() {
  const poolsBody = document.getElementById('investmentPoolsBody');
  if (!poolsBody) return;

  const pools = window.dashboardData?.investment_pools || [];
  if (pools.length === 0) {
    poolsBody.innerHTML = `<tr><td colspan="6" class="text-center">No investment pools found</td></tr>`;
    updateElement('totalInvestedAmount', formatCurrency(0));
    updateElement('totalInterestEarned', formatCurrency(0));
    return;
  }

  let totalInvested = 0;
  let totalInterest = 0;
  poolsBody.innerHTML = '';

  pools.forEach(pool => {
    const interest = calculateCurrentInterest({
      date: pool.investment_date,
      amount: pool.amount,
      maturityDate: pool.maturity_date
    });

    totalInvested += pool.amount;
    totalInterest += interest;

    const row = document.createElement('tr');
    row.innerHTML = `
      <td>${formatDate(pool.investment_date)}</td>
      <td>${formatCurrency(pool.amount)}</td>
      <td>${pool.member_count} members</td>
      <td>${formatCurrency(interest)}</td>
      <td>${formatDate(pool.maturity_date)}</td>
      <td><span class="badge bg-${pool.status.toLowerCase() === 'active' ? 'success' : 'secondary'}">${pool.status}</span></td>
    `;
    poolsBody.appendChild(row);
  });

  updateElement('totalInvestedAmount', formatCurrency(totalInvested));
  updateElement('totalInterestEarned', formatCurrency(totalInterest));
}

function updateWeeklySavings() {
  // Optional: Add logic to populate weekly savings summary
}

function updateMembersOverview() {
  // Optional: Add logic for members overview on main dashboard
}

// ========== Member Dashboard ==========
function updateMemberDashboard() {
  if (window.memberData) {
    updateMemberOverviewCards(window.memberData);
    updateTransactionsTable(window.memberData.transactions);
  }
}

function updateMemberOverviewCards(data) {
  updateElement('personalSavings', formatCurrency(data.totalSaved));
  updateElement('currentWeek', `Week ${data.currentWeek}`);
  updateElement('carryForward', formatCurrency(data.carryForward));
  const bar = document.getElementById('savingsProgress');
  if (bar) bar.style.width = `${data.progressPercentage}%`;
}

function updateTransactionsTable(transactions) {
  const tbody = document.querySelector('#savingsHistoryTable tbody');
  if (!tbody || !transactions) return;

  tbody.innerHTML = transactions.map(t => `
    <tr>
      <td>${t.date_saved}</td>
      <td>${formatCurrency(t.amount)}</td>
      <td>${formatCurrency(t.cumulative_total)}</td>
      <td>${t.weeks_covered}</td>
      <td>
        <span class="badge ${t.status === 'Complete' ? 'bg-success' : 'bg-warning'}">${t.status}</span>
      </td>
      <td>${formatCurrency(t.remaining_balance)}</td>
    </tr>
  `).join('');
}

// ========== Members Page ==========
function initializeMembersPage() {
  loadMembersData();

  const searchInput = document.getElementById("searchMember");
  if (searchInput) {
    searchInput.addEventListener("keydown", function (e) {
      if (e.key === "Enter") {
        const query = e.target.value.trim();
        searchMembers(query);
      }
    });

    document.querySelector("#searchMember + button")?.addEventListener("click", function () {
      const query = searchInput.value.trim();
      searchMembers(query);
    });
  }
}

function loadMembersData() {
  const tableBody = document.getElementById("membersTableBody");
  tableBody.innerHTML = `<tr><td colspan="6" class="text-center">Loading...</td></tr>`;

  fetch("/members-data/")
    .then((response) => response.json())
    .then((data) => {
      populateMembersTable(data.results);
      const stats = data.stats;
      if (stats) {
        updateElement("totalMembers", stats.total_members);
        updateElement("averageSavings", `UGX ${parseFloat(stats.average_savings).toLocaleString()}`);
        updateElement("averageWeeks", stats.average_weeks);
      }
    })
    .catch((error) => {
      console.error("Failed to load members:", error);
    });
}

function searchMembers(query) {
  if (!query) {
    loadMembersData(); // Reload all if query is empty
    return;
  }

  fetch(`/search-members/?q=${encodeURIComponent(query)}`)
    .then(response => response.json())
    .then(data => {
      populateMembersTable(data.results, "No matching members found.");
    })
    .catch(error => {
      console.error("Search error:", error);
    });
}

function populateMembersTable(members, message = "No members found.") {
  const tableBody = document.getElementById("membersTableBody");
  tableBody.innerHTML = "";

  if (members.length === 0) {
    tableBody.innerHTML = `<tr><td colspan="6" class="text-center text-muted">${message}</td></tr>`;
    return;
  }

  members.forEach((member) => {
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td>${member.member_name}</td>
      <td>${member.total_savings}</td>
      <td>${member.weeks_covered}</td>
      <td>${member.progress}</td>
      <td>${member.last_contribution}</td>
      <td>
        <span class="badge bg-${member.status === "Verified" ? "success" : "warning"}">${member.status}</span>
      </td>
    `;
    tableBody.appendChild(tr);
  });
}

// ========== Utilities ==========
function updateElement(id, value) {
  const el = document.getElementById(id);
  if (el) el.textContent = value;
}

function formatCurrency(amount) {
  return `UGX ${parseFloat(amount || 0).toLocaleString()}`;
}

function formatDate(dateString) {
  return new Date(dateString).toLocaleDateString("en-UG", {
    year: "numeric",
    month: "short",
    day: "numeric",
  });
}

function calculateCurrentInterest(investment) {
  const startDate = new Date(investment.date);
  const maturityDate = new Date(investment.maturityDate);
  const today = new Date();

  const totalDays = (maturityDate - startDate) / (1000 * 60 * 60 * 24);
  const elapsedDays = (today - startDate) / (1000 * 60 * 60 * 24);

  return investment.amount * 0.30 * (elapsedDays / totalDays);
}
  